from sqlalchemy import Column, Boolean, String, DateTime, Integer, Enum, ForeignKey,PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT
import enum 

Base = declarative_base()

class Displayname(enum.Enum):
    morning = 0
    day = 1
    midnight = 2
    earlymorning = 3
    

class Status(enum.Enum):
    inactive = 0
    active = 1

class Groups(Base):
    __tablename__ = 'groups'
    group_id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(50))


class Sessions(Base):
    __tablename__ = 'sessions'
    session_id = Column(Integer, primary_key=True,autoincrement=True)
    display_name = Column(Enum(Displayname))
    interval = Column(String(30))

class GroupProducts(Base):
    __tablename__ = 'group_products'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer)
    product_name = Column(String(50))
    product_code = Column(String(50))
    group_id = Column(Integer,ForeignKey(Groups.group_id))
    module_id = Column(Integer)
    status = Column(Boolean)
           


class MoniterSchedule(Base):
    __tablename__ = 'moniter_schedule'
    id = Column(Integer, primary_key=True,autoincrement=True)
    group_product_id = Column(Integer,ForeignKey(GroupProducts.id))
    check_interval = Column(Integer)
    session_id = Column(Integer, ForeignKey(Sessions.session_id))
    exclude_days = Column(String(20))

class GroupMailProperties(Base):
    __tablename__ = 'group_mail_properties'
    id = Column(Integer, primary_key=True,autoincrement=True) 
    group_id = Column(Integer,ForeignKey(Groups.group_id))
    mail_subject = Column(String(255))
    mail_to = Column(String(255))
    mail_cc = Column(String(255))
    mail_bcc = Column(String(255))
    mail_body = Column(LONGTEXT)


class ProductsLastTransactionsdetails(Base):
    __tablename__ = 'products_last_transactions_details'
    module_id = Column(Integer,primary_key=True)
    product_id = Column(Integer,primary_key=True)
    last_transaction_date = Column(DateTime)
    sent = Column(Boolean)


class ProductsLastTransactionshistory(Base):
    __tablename__ = 'products_last_transactions_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer)
    product_id = Column(Integer)
    last_transaction_date = Column(DateTime)


if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from sqlalchemy import create_engine
    from configurations import db_connection

    Base.metadata.create_all(bind=create_engine(db_connection('CONNECT_METASTORE'), echo=True))
