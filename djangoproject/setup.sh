#!/bin/bash

# EB environment
DB_USER=$1                # RDS database user
DB_PWD=$2                 # RDS database pwd
# vespa-app specific
DJANGO_SECRET_KEY=$3      # django app secret key
VESPA_SU_NAME=$4          # user name vespawatch applicatie superuser
VESPA_SU_PWD=$5           # paswoord vespawatch applicatie superuser

# create environment
eb create --cname vespawatch-dev --database --database.username $DB_USER --database.password $DB_PWD --database.size 5 --database.engine postgres --elb-type classic --envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD --region eu-west-1 --vpc  --vpc.dbsubnets subnet-2b338273,subnet-2ce39448,subnet-d0c6a5a6 --vpc.ec2subnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe --vpc.elbsubnets subnet-b74dfcef,subnet-53e39437,subnet-fcc6a58a --vpc.id vpc-cc8610a8 --vpc.securitygroups sg-ca7ae0b2,sg-4b8f442d --instance_profile aws-elasticbeanstalk-ec2-role-vespawatch --keyname LW-INBO-VESPAWATCH-DEV --tags APPLICATION=VESPAWATCH,ENVIRONMENT=DEV,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE

# Deploy the django app
eb deploy --message "Initiate Django app first deployment"