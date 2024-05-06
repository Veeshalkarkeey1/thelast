from models import GroupProducts,ProductsLastTransactionsdetails, ProductsLastTransactionshistory,GroupMailProperties ,MoniterSchedule,Sessions
from sqlalchemy import select,func,text,and_,or_,String
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session, aliased
from datetime import datetime,timedelta
from .weekday_enum import DaysOfWeek
from utils import logger


current_time = datetime.now().strftime("%H:%M:%S") 


# queries to check the last transaction date
last_txn_query = """
SELECT 
    te.product_id, 
    MAX(te.created_date) AS last_transaction_date, 
    te.module_id,
    0 AS sent
FROM 
    esewa_kernel.transaction_entries te
FORCE INDEX(idx_created_date)
WHERE 
    te.status = 1
    AND te.created_date BETWEEN NOW() - INTERVAL 5 MINUTE AND NOW()
    AND te.module_id IN (#module_ids#)
    AND te.product_id IN (#product_ids#) 
GROUP BY 
    te.product_id"""


def update_last_transaction_datetime(session_metastore, engine_datastore):
    """
    Fetches products that are active from metastore, checks their last transaction date from datastore and update the time on metastore
    """
    try: 
        group_config_runtime = aliased(Sessions)
        group_config_excludedays =aliased(MoniterSchedule)

        # Subquery for fetching products
        subquery_products = (select(GroupProducts.product_id) 
                .where(GroupProducts.id == group_config_excludedays.group_product_id, GroupProducts.status == 1)
                .group_by(GroupProducts.product_id)
                .scalar_subquery())
        
        #subquery for fetching modules
        subquery_module = (select(GroupProducts.module_id) 
                .where(GroupProducts.id == group_config_excludedays.group_product_id, GroupProducts.status == 1)
                .group_by(GroupProducts.product_id)
                .scalar_subquery())

        # Query to fetch metadata
        metadata_query = (select(
                subquery_module.label('modules'),
                subquery_products.label('products'),
                group_config_runtime.interval.label('config'),
                group_config_excludedays.exclude_days)
               .where(group_config_excludedays.session_id == group_config_runtime.session_id))
        

        logger.debug(metadata_query)

        result=session_metastore.execute(metadata_query).all()
        logger.debug(str(result))

  
        products = []
        modules = []
        for data in result:
            parsed_configs = {}
            for conf in data.config.split(','):
                split_config = conf.split('-')  
                start_time = split_config[0]  
                end_time = split_config[1]  
                parsed_configs[start_time] = end_time
            exclude_list = data.exclude_days
            conditional_filter = False if exclude_list is None else str(DaysOfWeek(datetime.today().weekday()).name) in exclude_list.split(',')
            for start_time, end_time in parsed_configs.items():
                if current_time > start_time and current_time < end_time and not conditional_filter and not products is None :
                    if data.products is not None and data.modules is not None: 
                        products.append(data.products)
                        modules.append(data.modules) 
                    else:
                        logger.info(f"The product status is inactive")

    
        #got the list of products to check for last transaction     
        if products :
            module_product_list = [(module_id, product_id) for module_id, product_id in zip(modules, products)]
            logger.info(f"Active modules and productes: {module_product_list}")
            merchant_product = ''
            bank_product = ''
            for module_id, product_id in module_product_list:
                if module_id == 1:
                  merchant_product =  merchant_product + str(product_id) + ',' 
                else:
                    bank_product =  bank_product + str(product_id) + ',' 
            merchant_product = merchant_product.rstrip(',')
            bank_product = bank_product.rstrip(',')


            last_transaction_data_merchant = []
            last_transaction_data_bank = []
            if merchant_product:
                replace_merchant = last_txn_query.replace('#product_ids#', merchant_product).replace('#module_ids#', '1')
                with Session(engine_datastore) as session_datastore:
                    last_transaction_data_merchant = session_datastore.execute(replace_merchant).all()



            if bank_product:
                replace_bank = last_txn_query.replace('#product_ids#', bank_product).replace('#module_ids#', '2')
                with Session(engine_datastore) as session_datastore:
                    last_transaction_data_bank = session_datastore.execute(replace_bank).all()

            combined_transaction_data = last_transaction_data_merchant + last_transaction_data_bank




            if not len(combined_transaction_data) == 0:
                for data in combined_transaction_data:
                    # Insert into ProductsLastTransactionsHistory
                    try:
                        session_metastore.execute(
                            insert(ProductsLastTransactionshistory).values(
                                product_id=data.product_id,
                                last_transaction_date = data.last_transaction_date,
                                module_id = data.module_id))
                        session_metastore.commit()
                    except Exception as e:
                        session_metastore.rollback()
                        logger.exception(e)
                    # Update ProductsLastTransactionsDetails
                    try:
                        session_metastore.execute(
                            insert(ProductsLastTransactionsdetails)
                            .values(
                                product_id=data.product_id,
                                module_id=data.module_id,
                                last_transaction_date = data.last_transaction_date,
                                sent=data.sent)
                            .on_duplicate_key_update(
                                last_transaction_date = data.last_transaction_date,
                                sent=data.sent))
                        session_metastore.commit()
                    except Exception as e:
                        session_metastore.rollback()
                        logger.exception(e)
            logger.info("Updated last transactions for active products")
            return products
        else:
            logger.debug("No active product")
            return
    except Exception as e:
        logger.exception(e)


def get_problematic_products_from_metastore(session_metastore, products):
    logger.info("Fetching problematic products from metastore")
    
    #query for the current session_id corresponding to the current time
    query_current_session_id = (select(Sessions.session_id)
        .where(func.substr(Sessions.interval, 1, 8) <=  current_time)
        .where(func.substr(Sessions.interval, 10, 8) >= current_time))
    
    current_session_id = session_metastore.execute(query_current_session_id).scalar()

    if current_session_id:
        logger.info(f"Current Session ID: {str(current_session_id)}")
    else:
        logger.info("No session is currently active.")

    
    query_problematic_products = (select(
            GroupProducts.group_id,
            GroupProducts.product_id,
            GroupProducts.product_name,
            GroupProducts.product_code,
            GroupProducts.module_id,
            Sessions.session_id,
            MoniterSchedule.check_interval,
            ProductsLastTransactionsdetails.last_transaction_date)
        .join(GroupProducts,GroupProducts.id == MoniterSchedule.group_product_id)
        .join(ProductsLastTransactionsdetails,and_(ProductsLastTransactionsdetails.product_id == GroupProducts.product_id,ProductsLastTransactionsdetails.module_id == GroupProducts.module_id))
        .join(Sessions, Sessions.session_id == MoniterSchedule.session_id)
        .where(
                GroupProducts.status == 1,
                ProductsLastTransactionsdetails.product_id.in_(products),
                ProductsLastTransactionsdetails.sent == False,
                MoniterSchedule.session_id == current_session_id)
        .having(
                func.TIMESTAMPDIFF(text('SECOND'), ProductsLastTransactionsdetails.last_transaction_date, func.NOW()) > MoniterSchedule.check_interval))

    logger.debug("Query for fetching problematic products")
    logger.debug(query_problematic_products)
    result_problematic_products = session_metastore.execute(query_problematic_products).all()

    #here we have got the list of probematic products. Now preparing for mail
    logger.debug("Fetched Problematic Products")
    logger.debug(result_problematic_products)



    problematic_groups = set()
    for result in result_problematic_products:
        problematic_groups.add(result.group_id)
    problematic_groups = list(problematic_groups)



    # fetching mail details for problematic groups
    query_mail_details = select(GroupMailProperties).where(GroupMailProperties.group_id.in_(problematic_groups))
    


    logger.debug(f"Problematic Groups: {problematic_groups}")
    result_mail_details = session_metastore.execute(query_mail_details).all()
    logger.debug(f"Query Problematic Groups {query_mail_details}")
    logger.debug(f"Data for problematic groups {result_mail_details}")
    logger.info("Fetched data for problematic groups")
    return result_problematic_products, result_mail_details

