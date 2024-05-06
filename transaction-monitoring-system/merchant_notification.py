from utils import logger, update_last_transaction_datetime, get_problematic_products_from_metastore, send_mail_html
from models import ProductsLastTransactionsdetails
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
from configurations import *

if __name__ == "__main__":
    try:
        logger.info("Application Started, Fetching application properties")
        
        # create sqlalchemy engines
        engine_metastore = create_engine(db_connection('CONNECT_METASTORE'), echo=False)
        engine_datastore = create_engine(db_connection('CONNECT_DB_23'), echo=False)
        result_problematic_products = None
       
        # Fetch last transaction datetime and problematic products
        with Session(engine_metastore) as session_metastore:
            products = update_last_transaction_datetime(session_metastore, engine_datastore)
            if products:
                result_problematic_products, result_mail_details = get_problematic_products_from_metastore(session_metastore, products)

        # processing for sending mail
        if result_problematic_products and result_mail_details:
            logger.info("Sending Email Now")
            for groups in result_mail_details:
                products_formatted_table = ''
                module_ids = ''
                product_codes = ''
                product_ids = ''
                for product in result_problematic_products:
                    if product.group_id == groups.GroupMailProperties.group_id:   
                            if product.module_id ==1:
                                module_name = 'Merchant'
                            elif product.module_id ==2:
                                module_name = 'Bank'
                            else:
                                module_name = 'Unknown'
                            module_ids = module_ids+str(product.module_id)+','
                            product_ids = product_ids+str(product.product_id)+','
                            product_codes = product_codes+product.product_code+','
                            products_formatted_table = products_formatted_table + f"<tr><td>{module_name}</td><td>{product.product_code}</td><td>{product.product_name}</td><td>{product.last_transaction_date}</td></tr>"

                #send the mail 
                mail_body = groups.GroupMailProperties.mail_body.replace('{table_rows}', products_formatted_table)
                is_sent = send_mail_html(mail_to=groups.GroupMailProperties.mail_to, subject=groups.GroupMailProperties.mail_subject, html_message=mail_body, mail_cc=groups.GroupMailProperties.mail_cc, mail_bcc=groups.GroupMailProperties.mail_bcc)

                # Update sent status in the database
                if is_sent:
                    with Session(engine_metastore) as session_metastore:
                        sent_update_query = update(ProductsLastTransactionsdetails).where(ProductsLastTransactionsdetails.product_id.in_(product_ids.rstrip(',').split(','))).values(sent=True)
                        logger.debug(f"Update query for sent: {sent_update_query}")
                        session_metastore.execute(
                            sent_update_query)
                        session_metastore.commit()
                logger.info(f"Email sent for group {groups.GroupMailProperties.group_id}, Module Id: {module_ids.rstrip(',')}, product_codes: {product_codes.rstrip(',')}")
        else:
            logger.info("All Products are Working Fine")
    except Exception as e:
        logger.exception(e)


