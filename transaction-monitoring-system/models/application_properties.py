from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String
from sqlalchemy import create_engine, Column, BigInteger, Integer, Float, DateTime, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class TransactionEntry(Base):
    __tablename__ = 'transaction_entries'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_date = Column(DateTime)
    last_modified_date = Column(DateTime)
    version = Column(BigInteger)
    amount = Column(Float, nullable=False)
    channel = Column(Integer)
    last_error = Column(String(1000))
    module_id = Column(Integer, nullable=False)
    payer_account_id = Column(BigInteger)
    payer_cas_id = Column(BigInteger)
    product_id = Column(BigInteger)
    product_type_id = Column(Integer)
    receiver_account_id = Column(BigInteger)
    receiver_cas_id = Column(BigInteger)
    reward_point = Column(Float)
    status = Column(Integer)
    unique_id = Column(String(255))
    narration_id = Column(BigInteger)
    transactor_module_id = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint('unique_id', name='UK_7svjkgi24rbjjpoyf6sgpdnux'),
        Index ('FK5v6ffy4xd7xmvr6r6iwhdmx1o','narration_id'),
        Index('idx_created_date', 'created_date'),
        Index('idx_last_modified_date', 'last_modified_date'),
        Index('idx_product_id', 'product_id'),
        Index('idx_payer_account_id', 'payer_account_id'),
        Index('idx_receiver_account_id', 'receiver_account_id')
    )

if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from sqlalchemy import create_engine
    from configurations import db_connection

    Base.metadata.create_all(bind=create_engine(db_connection('CONNECT_DB_23'), echo=True))
