from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator

class BaseTransactionEvent(BaseModel):
    transaction_id: str = Field(..., description='Unique UUIDv4 for identifying the transaction')
    event_name: str = Field(..., description='Event category')
    timestamp: datetime = Field(..., description='UTC timestamp for transaction')
    currency: Literal['PHP'] = Field(..., description='Accepted currency code')

class FundTransferEvent(BaseTransactionEvent):
    source_account_id: str = Field(..., description='Sender account identifier')
    destination_account_id: str = Field(..., description='Recipient account identifier')
    amount: Decimal = Field(..., gt=Decimal('0.00'), description='Positive transfer amount')
    channel: Literal['instapay', 'pesonet', 'qr_ph', 'card'] = Field(..., description='Designated clearing network')

    # nullable, optional field
    fee: Optional[Decimal] = Field(None, gt=Decimal('0.00'), description='Processing fee')

    @model_validator(mode='after') # rule for account sending money to itself
    def prevent_self_transfers(self) -> 'FundTransferEvent':
        if self.source_account_id == self.destination_account_id:
            raise ValueError(
                f'Self-transfer prohibited: destination matches source ({self.source_account_id}).'
            )
        return self