from db_insert import insert_file_to_db, insert_user_to_db, insert_company_to_db
from db_connection import session
import os


# insert_company_to_db(1, "Dotlines", session)
# insert_user_to_db(1, "Alice", session)

file_dir="documents"

for file_name in os.listdir(file_dir):
    file_path= os.path.join(file_dir, file_name)
    insert_file_to_db(file_path=file_path, company_id=1, session=session)