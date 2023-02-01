#!/bin/python3
import boto3
import requests

instance_id = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
instance_id = instance_id.text

region = requests.get('http://169.254.169.254/latest/meta-data/placement/region')
region = region.text

ssm_client = boto3.client('ssm', region_name=f"{region}")

ec2 = boto3.resource('ec2', region_name=f"{region}")

s3_client = boto3.client('s3')

tag = ""

for get_tag in list(ec2.instances.filter(InstanceIds=[f"{instance_id}"])):

    tag = tag + get_tag.tags[0]['Value']



class ENV:

        def  __init__(self,RDS_DB_NAME,RDS_USERNAME,RDS_PASSWORD,RDS_HOSTNAME,JARNAME):

                self.RDS_DB_NAME = RDS_DB_NAME
                self.RDS_USERNAME = RDS_USERNAME
                self.RDS_PASSWORD = RDS_PASSWORD
                self.RDS_HOSTNAME = RDS_HOSTNAME
        
        def get_env(self):

                RDS_DB_NAME = ssm_client.get_parameter(Name=f"{self.RDS_DB_NAME}",WithDecryption=True)['Parameter']['Value']
                RDS_USERNAME = ssm_client.get_parameter(Name=f"{self.RDS_USERNAME}",WithDecryption=True)['Parameter']['Value']
                RDS_PASSWORD = ssm_client.get_parameter(Name=f"{self.RDS_PASSWORD}",WithDecryption=True)['Parameter']['Value']
                RDS_HOSTNAME = ssm_client.get_parameter(Name=f"{self.RDS_HOSTNAME}",WithDecryption=True)['Parameter']['Value']

                return "AWS_RDS_HOSTNAME={}".format(RDS_HOSTNAME) + '\n' + "AWS_RDS_PASSWORD={}".format(RDS_PASSWORD) + '\n' + "AWS_RDS_USERNAME={}".format(RDS_USERNAME) + '\n' + "AWS_RDS_DB_NAME={}".format(RDS_DB_NAME) + '\n' + "AWS_API_JARNAME={}".format(JARNAME)

BUCKET_DEV = ssm_client.get_parameter(Name="/DEV/BUCKET_NAME",WithDecryption=True)['Parameter']['Value']
TAG_DEV = ssm_client.get_parameter(Name="/DEV/TAG_NAME",WithDecryption=True)['Parameter']['Value']
JARNAME = ssm_client.get_parameter(Name="JAR_NAME",WithDecryption=True)['Parameter']['Value']
BUCKET_PROD = ssm_client.get_parameter(Name="/PROD/BUCKET_NAME",WithDecryption=True)['Parameter']['Value']
TAG_PROD = ssm_client.get_parameter(Name="/PROD/TAG_NAME",WithDecryption=True)['Parameter']['Value']


if TAG_DEV == tag:
  s3_client.download_file(f"{BUCKET_DEV}", f"{JARNAME}", f"/opt/deploy/{JARNAME}")
  dev = ENV("/DEV/DB_NAME","/DEV/DB_USERNAME","/DEV/DB_PASSWD","/DEV/DB_HOSTNAME",JARNAME)
  f = open("/etc/environment", "w")
  f.write(dev.get_env())
  f.close()

if TAG_PROD == tag:
  s3_client.download_file(f"{BUCKET_PROD}", f"{JARNAME}", f"/opt/deploy/{JARNAME}")
  prod = ENV("/PROD/DB_NAME","/PROD/DB_USERNAME","/PROD/DB_PASSWD","/PROD/DB_HOSTNAME",JARNAME)
  f = open("/etc/environment", "w")
  f.write(prod.get_env())
  f.close()
