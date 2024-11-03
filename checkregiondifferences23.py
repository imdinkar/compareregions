
#Python script to list the differnces of services and features between two AWS region
# Script uses AWS boto3 SDK.
import boto3
import csv
import time
from botocore.exceptions import ClientError

def list_used_services_and_features(session):
    
    client = session.client('service-quotas') 

    # To Get the list of services available in the region
    paginator = client.get_paginator('list_services')
    service_names = []
    for page in paginator.paginate():
        service_names.extend(page['Services'])

    # To Get the used features for each service
    used_features = {}
    for service in service_names:
        service_code = service['ServiceCode']
        service_name = service['ServiceName']
        quotas = list_service_quotas_with_retries(client, ServiceCode=service_code)
        if quotas is not None:
            for quota in quotas:
                if quota.get('Value', 0) > 0:
                    used_features[service_name] = {quota['QuotaName']: 'Available'}
                    break

    return used_features

def check_services_and_features_in_region(access_key, secret_key, source_region, target_region):
    # To Create session with specified credentials and source region
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=source_region
    )

    # To Get the used services and features in the source region
    source_used_features = list_used_services_and_features(session)

    # Create session with specified credentials and target region
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=target_region
    )

    # Get used services and features in the target region
    target_used_features = list_used_services_and_features(session)

    # to export the differences create a csv file
    with open('differences23.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Service', 'Feature', 'Status'])

        # Check if each used service in the source region is available in the target region
        for service_name, source_features in source_used_features.items():
            target_features = target_used_features.get(service_name, {})
            # Check if each used feature in the source region is available in the target region
            for feature, source_status in source_features.items():
                target_status = target_features.get(feature, 'Not Available')
                if target_status == 'Not Available':
                    writer.writerow([service_name, feature, 'Available in source_region, Not Available in target_region'])
                    
                
                #writer.writerow([service_name, feature, "Available in" +" "+ source_region +" "," "Not Available" +" "+ target_region +"])
                    #"Hello" +" "+ language +" "+ "World!"
                    #writer.writerow([service_name, feature, "Available in + source_region ", Not Available in {target_region}'])
                else:
                    writer.writerow([service_name, feature, 'Available in both the region'])

##Function to retry for api quota limits with some random delay to spread the retries
def list_service_quotas_with_retries(client, **kwargs):
    retries = 5
    for i in range(retries):
        try:
            quotas = client.list_service_quotas(**kwargs)['Quotas']
            return quotas
        except ClientError as e:
            if e.response['Error']['Code'] == 'Throttling':
                if i < retries - 1:
                    delay = (2 ** i) * 0.1  # Exponential backoff with jitter
                    time.sleep(delay)
                else:
                    raise e

if __name__ == "__main__":
    # Provide your AWS access key, secret key
    access_key = 'provide-your-access-key'
    secret_key = 'provide-your-secret-key'
    source_region = 'ap-south-1'  # Replace with the source region where you want to check used services and features
    target_region = 'ap-south-2'  # Replace with the target region you want to check against
    check_services_and_features_in_region(access_key, secret_key, source_region, target_region)
    print("Differences exported to differences23.csv")