

elastic beanstalk
    * Python 3.6


RESOURCES:
    * RDS postgresql  + eigen backup,...
    * S3 voor uploaded images + eigen backup
    *

## Tutorial info

* https://realpython.com/deploying-a-django-app-and-postgresql-to-aws-elastic-beanstalk/
* https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-container.html


## Installation



https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html



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

# create the S3 media storage bucket

To store the media files, we use a S3 Bucket. This need to be setup the first time:

```
aws s3api create-bucket --bucket lw-vespawatch --region eu-west-1 --create-bucket-configuration LocationConstraint=eu-west-1 --acl private
aws s3api put-bucket-tagging --bucket lw-vespawatch --tagging file://s3-tags.json
```

see https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings

# Prepare the ec2 instance profile (role) to access the S3 bucket

Without providing a `instance-role`, the default is used. However, as we have multiple eb running at inbo, the default instance role (what the EC2 machine is allowed to do) would get mixed permissions attahced to it. Hence, we define a custom service role and attach the S3 permissions to it:

As such, we have to create a custom permission for access to S3 bucket and attach this to an `Instance Profile` for the ec2 machines

https://docs.aws.amazon.com/cli/latest/reference/iam/create-instance-profile.html

* create the instance profile for vespawatch
* create a custom role with the S3 access to vespawatch permission
* add the policies from aws-elasticbeanstalk-ec2-role to the custom role
* attach custom role to the instance profile

```
# create the custom instance role
aws iam create-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch

# create a custom vespawatch aws-elasticbeanstalk-ec2-role
aws iam create-role --role-name aws-elasticbeanstalk-ec2-role-vespawatch --assume-role-policy-document file://ec2-trust-policy.json --description 'vespawatch application role'

# add the S3 access rule
aws iam put-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-name lw-vespawatch-s3 --policy-document file://s3-policy.json

# add the required elasticbeanstalk policies
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkMulticontainerDocker
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkWorkerTier
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::226308051916:policy/AWS-Beanstalk-Volumes

# attach the custom vespawatch aws-elasticbeanstalk-ec2-role
aws iam add-role-to-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch --role-name aws-elasticbeanstalk-ec2-role-vespawatch
```

check it with `aws iam list-instance-profiles`

INFO:
* https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/iam-instanceprofile.html
* https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html

If you manage your roles from the AWS CLI or the AWS API, you create roles and instance profiles as separate actions. Because roles and instance profiles can have different names, you must know the names of your instance profiles as well as the names of roles they contain. That way you can choose the correct instance profile when you launch an EC2 instance.

# create environment

```
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
--instance_profile aws-elasticbeanstalk-ec2-role-vespawatch
--keyname LW-INBO-VESPAWATCH-DEV
--tags APPLICATION=VESPAWATCH,ENVIRONMENT=DEV,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
```

# TODO -> voor ec2 en elb dus beide de dev private subnets en voor rds diegene die je al gebruikte (die hebben alleen private subnets)


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




