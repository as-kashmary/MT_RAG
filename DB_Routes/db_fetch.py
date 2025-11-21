from db_connection import session, File, Company, User
import os

def fetch_file_by_company(company_id, session):
    files = session.query(File).filter_by(company_id=company_id).all()
    return files

def fetch_file_by_pending_status(pending_status, session):
    files = session.query(File).filter_by(pending=pending_status).all()
    return files

def fetch_file_by_failed_status(failed_status, session):
    files = session.query(File).filter_by(failed=failed_status).all()
    return files

def fetch_file_by_successful_status(successful_status, session):
    files = session.query(File).filter_by(successful=successful_status).all()
    return files

def fetch_company_by_name(company_name, session):
    company = session.query(Company).filter_by(name=company_name).first()
    return company

def fetch_file_by_company_pending(company_id, session):
    files= session.query(File).filter_by(company_id=company_id, pending=True).all()
    return files