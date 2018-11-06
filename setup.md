

elastic beanstalk
    * Python 3.6


RESOURCES:
    * RDS postgresql  + eigen backup,...
    * S3 voor uploaded images + eigen backup
    *

## Tutorial info

* https://realpython.com/deploying-a-django-app-and-postgresql-to-aws-elastic-beanstalk/
* https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-container.html


## elastic beanstalk create environment

* info on the create
https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb3-create.html

For each settings, using INBO dev settings coming from VPC info
https://github.com/inbo/cloudformation-templates/tree/master/config/vpc
! bastion van DEV


-----------------------------
Variabelen:
$DB_USER # RDS database user
$DB_PWD  # RDS database pwd
$DJANGO_SECRET_KEY   # django app secret key
$VESPA_SU_NAME  # user name vespawatch applicatie superuser
$VESPA_SU_PWD # paswoord vespawatch applicatie superuser

# create environment

eb create
--cname vespawatch-dev
--database --database.username $DB_USER --database.password $DB_PWD
--database.size 5
--database.engine postgres
--elb-type classic
--envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD
--region eu-west-1
--vpc
--vpc.dbsubnets subnet-2b338273,subnet-2ce39448,subnet-d0c6a5a6
--vpc.ec2subnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe
--vpc.elbsubnets subnet-b74dfcef,subnet-53e39437,subnet-fcc6a58a
--vpc.id vpc-cc8610a8
--vpc.securitygroups sg-ca7ae0b2,sg-4b8f442d
--keyname LW-INBO-VESPAWATCH-DEV
--tags APPLICATION=VESPAWATCH,ENVIRONMENT=DEV,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE

# Deploy the django app

eb deploy --message "Initiate Django app first deployment"

--------------------------
./deployment.sh vespawatch vespawatch KEEPTHISDJANGOKEYSECRET vespawatch vespawatch

Enter Environment Name
(default is vespawatch-dev):

Do you want to associate a public IP address? (Y/n): Y
Do you want the load balancer to be public? (Select no for internal) (Y/n): Y


TODO: https://medium.com/@nqbao/how-to-use-aws-ssm-parameter-store-easily-in-python-94fda04fea84

* wat met de backup van de RDS - op organisatieniveau geregeld
* OWNER en BUSINESS_UNIT kunnen we zelf instellen en gebruiken voor kostenrapportering

##
! need to create key-pair and use that one?
! settings file location is environmental variable

## S3 for media files

https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings

