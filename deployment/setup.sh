#!/bin/bash

# deploy environment
ENVIRONMENT=$1
# EB environment
DB_USER=$2                # RDS database user
DB_PWD=$43                # RDS database pwd
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
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::226308051916:policy/AWS-Beanstalk-Volumes
aws iam add-role-to-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch --role-name aws-elasticbeanstalk-ec2-role-vespawatch

# create the eb environment
if [ $ENVIRONMENT = "dev" ]; then
    cp ../djangoproject/settings/settings_dev.py ../djangoproject/settings/settings.py
    # create environment
    eb create --cname vespawatch-dev --database --database.username $DB_USER --database.password $DB_PWD --elb-type classic --envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,ENVIRONMENT=$ENVIRONMENT --region eu-west-1 --vpc --vpc.dbsubnets subnet-2b338273,subnet-2ce39448,subnet-d0c6a5a6 --vpc.ec2subnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe --vpc.elbsubnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe --vpc.id vpc-cc8610a8 --vpc.securitygroups sg-ca7ae0b2,sg-4b8f442d --tags APPLICATION=VESPAWATCH,ENVIRONMENT=DEV,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE

elif [ $ENVIRONMENT = "uat" ]; then
    cp ../djangoproject/settings/settings_uat.py ../djangoproject/settings/settings.py
    eb create --cname vespawatch-uat --database --database.username $DB_USER --database.password $DB_PWD --elb-type classic --envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,ENVIRONMENT=$ENVIRONMENT --region eu-west-1 --vpc --vpc.dbsubnets subnet-f54dfcad,subnet-14f98e70,subnet-e7fc9f91 --vpc.ec2subnets subnet-994afbc1,subnet-5cf98e38,subnet-2efc9f58 --vpc.elbsubnets subnet-994afbc1,subnet-5cf98e38,subnet-2efc9f58 --vpc.id vpc-a58610c1 --vpc.securitygroups sg-cf47ddb7,sg-8a9346ec --keyname LW-INBO-VESPAWATCH-UAT --tags APPLICATION=VESPAWATCH,ENVIRONMENT=UAT,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE

else # ! subnets en vpc aanpassen!
    cp ../djangoproject/settings/settings_prd.py ../djangoproject/settings/settings.py
    eb create --cname vespawatch-prd --database --database.username $DB_USER --database.password $DB_PWD --elb-type classic --envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD,ENVIRONMENT=$ENVIRONMENT --region eu-west-1 --vpc --vpc.dbsubnets subnet-7a763f23,subnet-c4f6ffa1,subnet-9a0a3bed --vpc.ec2subnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb --vpc.elbsubnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb --vpc.id vpc-79d0f71c --vpc.securitygroups sg-ce6ff5b6,sg-35d5ed51 --tags APPLICATION=VESPAWATCH,ENVIRONMENT=PRD,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
fi

# Deploy the django app
eb deploy --message "Initiate Django app first deployment"

# setup the firefighters polygons and user accounts
eb ssh --command "source /opt/python/run/venv/bin/activate && python ../manage.py import_firefighters_zones ../data/Brandweerzones_2019.geojson"
eb ssh --command "source /opt/python/run/venv/bin/activate && python ../manage.py create_firefighters_accounts"

# execute a first syncronization with iNaturalist to collect the ifirst set of data
eb ssh --command "source /opt/python/run/venv/bin/activate && python ../manage.py sync_pull"

# remove the inbound rule for ssh on port 22 (just an example)
# aws ec2 revoke-security-group-ingress --group-id sg-0ed982b15ae8893ef --protocol tcp --port 22 --cidr 0.0.0.0/0
