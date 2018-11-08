#!/bin/bash

# deploy environment
ENVIRONMENT=$1
# EB environment
DB_USER=$2                # RDS database user
DB_PWD=$3                 # RDS database pwd
# vespa-app specific
DJANGO_SECRET_KEY=$4      # django app secret key
VESPA_SU_NAME=$5          # user name vespawatch applicatie superuser
VESPA_SU_PWD=$6           # paswoord vespawatch applicatie superuser

# create s3 bucket for media file storage
aws s3api create-bucket --bucket lw-vespawatch --region eu-west-1 --create-bucket-configuration LocationConstraint=eu-west-1 --acl private
aws s3api put-bucket-tagging --bucket lw-vespawatch --tagging file://s3-tags.json

# create the instance profile with permissions
aws iam create-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch
aws iam create-role --role-name aws-elasticbeanstalk-ec2-role-vespawatch --assume-role-policy-document file://ec2-trust-policy.json --description 'vespawatch application role'
aws iam put-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-name lw-vespawatch-s3 --policy-document file://s3-policy.json
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkMulticontainerDocker
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkWorkerTier
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::226308051916:policy/AWS-Beanstalk-Volumes
aws iam add-role-to-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch --role-name aws-elasticbeanstalk-ec2-role-vespawatch

# create the eb environment
if [ $ENVIRONMENT = "dev" ]; then
    # create environment
    cp ../djangoproject/settings/settings_dev.py ../djangoproject/settings/settings.py
    eb create --cname vespawatch-dev --database --database.username $DB_USER --database.password $DB_PWD --database.size 5 --database.engine postgres --elb-type classic --envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD --region eu-west-1 --vpc  --vpc.dbsubnets subnet-2b338273,subnet-2ce39448,subnet-d0c6a5a6 --vpc.ec2subnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe --vpc.elbsubnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe --vpc.id vpc-cc8610a8 --vpc.securitygroups sg-ca7ae0b2,sg-4b8f442d --instance_profile aws-elasticbeanstalk-ec2-role-vespawatch --keyname LW-INBO-VESPAWATCH-DEV --tags APPLICATION=VESPAWATCH,ENVIRONMENT=DEV,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
else # ! subnets en vpc aanpassen!
    cp ../djangoproject/settings/settings_prd.py ../djangoproject/settings/settings.py
    eb create --cname vespawatch-prd --database --database.username $DB_USER --database.password $DB_PWD --database.size 5 --database.engine postgres --elb-type classic --envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD --region eu-west-1 --vpc  --vpc.dbsubnets subnet-7a763f23,subnet-c4f6ffa1,subnet-9a0a3bed --vpc.ec2subnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb --vpc.elbsubnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb --vpc.id vpc-79d0f71c --vpc.securitygroups sg-ce6ff5b6,sg-35d5ed51 --instance_profile aws-elasticbeanstalk-ec2-role-vespawatch --keyname LW-INBO-VESPAWATCH-PRD --tags APPLICATION=VESPAWATCH,ENVIRONMENT=PRD,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
fi

# Deploy the django app
eb deploy --message "Initiate Django app first deployment"
