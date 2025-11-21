from db_connection import session, File, Company, User

def update_file_status_running(file_id, running_status, session):
    file_record = session.query(File).filter_by(id=file_id).first()
    if file_record:
        file_record.running = running_status
        file_record.pending = not running_status
        session.commit()
        print(f"Updated running status for file ID {file_id} to {running_status}")
    else:
        print(f"No file found with ID {file_id}")

def update_file_status_successful(file_id, successful_status, session):
    file_record = session.query(File).filter_by(id=file_id).first()
    if file_record:
        file_record.successful = successful_status
        file_record.pending = not successful_status
        file_record.running = not successful_status
        session.commit()
        print(f"Updated successful status for file ID {file_id} to {successful_status}")
    else:
        print(f"No file found with ID {file_id}")

def update_file_status_failed(file_id, failed_status, session):
    file_record = session.query(File).filter_by(id=file_id).first()
    if file_record:
        file_record.failed = failed_status
        file_record.pending = not failed_status
        file_record.running = not failed_status
        file_record.successful = not failed_status
        session.commit()
        print(f"Updated failed status for file ID {file_id} to {failed_status}")
    else:
        print(f"No file found with ID {file_id}")

