from db_connection import session, File, Company, User

def update_file_status_running(file_id, session):
    file_record = session.query(File).filter_by(id=file_id).first()
    if file_record:
        file_record.status = "running"
        session.commit()
        print(f"Updated running status for file ID {file_id} to running ")
    else:
        print(f"No file found with ID {file_id}")

def update_file_status_successful(file_id, session):
    file_record = session.query(File).filter_by(id=file_id).first()
    if file_record:
        file_record.status = "successful"
        session.commit()
        print(f"Updated successful status for file ID {file_id} to successful")
    else:
        print(f"No file found with ID {file_id}")

def update_file_status_failed(file_id, session):
    file_record = session.query(File).filter_by(id=file_id).first()
    if file_record:
        file_record.status = "failed"
        session.commit()
        print(f"Updated failed status for file ID {file_id} to failed")
    else:
        print(f"No file found with ID {file_id}")

