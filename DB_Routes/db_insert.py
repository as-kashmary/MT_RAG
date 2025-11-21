from db_connection import session, File, Company, User
import os

# Example: upload a file
file_path = "documents/texts.txt"  # adjust to your local file
company_id = 1  # replace with a valid company_id in your DB



def insert_file_to_db(file_path, company_id, session):

    file_name= os.path.basename(file_path)
    file_type= file_name.split(".")[-1]
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    new_file = File(
        file_name=file_name,
        company_id=company_id,
        file_data=file_bytes,
        file_format=file_type,
        pending=True,
        running=False,
        successful=False,
        failed=False
    )

    session.add(new_file)
    session.commit()
    print("File uploaded successfully!")


def insert_user_to_db(id, name, session):
    new_user = User(
        id=id,
        name=name
    )

    session.add(new_user)
    session.commit()
    print("User uploaded successfully!")



def insert_company_to_db(id, name, session):
    new_company = Company(
        id=id,
        name=name
    )

    session.add(new_company)
    session.commit()
    print("Company uploaded successfully!")





# def query_on_file(file_id, session):
#     file_record = session.query(File).filter_by(id=file_id).first()
#     print(f"File name: {file_record.file_name}")


# file_record = session.query(File).filter_by(id=1).first()

# with open(file_record.file_name, "wb") as f:
#     f.write(file_record.file_data)

# print("File downloaded successfully!")

