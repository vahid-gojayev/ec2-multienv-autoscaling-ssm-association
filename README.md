# ec2-multienv-autoscaling-ssm-association



![ssm-dock-automation](https://user-images.githubusercontent.com/16609723/215979166-9bf5f12a-0776-4471-b835-6963a17ace24.jpg)

This project is an interesting way to automate.In this scenario I automated deploy  java spring boot.I used ssm document and simple python script.This approach gives us some advantages listed below

* Allow the same AMI to work in multiple environments
* Automatic deployment when starting a new instance
* Deploy with a simple command
* Deploy with  Scheduler

The current project is working on two environments: prod and test, but if you want to extend the environment, you can do so. Please see an example below. You can add a new if statement with a new environment to env.py.
    

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

If you not need other environment you should just add ssm parameter store with SecureString Type. Please use Environment Keys Listed Below

For Dev Environment:

      /DEV/DB_HOSTNAME=usermanager-dev.cs7sss7t6qd.us-east-1.rds.amazonaws.com
      /DEV/DB_NAME=usermanager
      /DEV/DB_PASSWD=password	
      /DEV/DB_USERNAME=root
      /DEV/TAG_NAME=usermgmt-dev-grp
      /DEV/BUCKET_NAME=usermanagerdev-bucket
    
For Prod Environment:

      /PROD/DB_HOSTNAME=usermanager-prod.cs7sss7t6qd.us-east-1.rds.amazonaws.com
      /PROD/DB_NAME=usermanager
      /PROD/DB_PASSWD=password	
      /PROD/DB_USERNAME=root
      /PROD/TAG_NAME=usermgmt-prod-grp
      /PROD/BUCKET_NAME=usermanagerprod-bucket

For General Environment:

Important! for jar file must be different bucket, in my case i used mulienv-script bucket, please change your bucket in usermgmt _document.json file

     JAR_NAME=usermgmt-mysql-v1.jar 
     
When starting the association, env.py is copied and run into instance, env.py gets the correct environment from ssm using the filter's autoscale tag, and imports into systemd.Please look at the script

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


Let's do that steps:
  
  1) Create Variables in Parameter Store  as Type SecureString
  2) Create 3 bucket for dev prod and scripts (for script bucket i explained you must change in usermgmt _document.json  file)
  3) Create LaunchConfig
  4) Create Autoscaling Group 
     
            aws autoscaling create-auto-scaling-group --auto-scaling-group-name usermgmt-dev-grp --launch-configuration-name Launch-Config-UserMgmt-Env --min-size 1 --max-size 3 --vpc-zone-identifier subnet-080d99487ebd3a923
      
  5) Create ssm document
  
            aws ssm create-document --name UsermgmtAutomationDocument --content file://usermgmt_document.json  --document-type Command
            
  6) Create association
            
            aws ssm create-association --name UsermgmtAutomationDocument --targets "Key=tag:aws:autoscaling:groupName,Values=usermgmt-dev-grp"



