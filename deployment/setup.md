
# Django app setup on AWS

## Introduction

The deployment is using elastic beanstalk on AWS to setup and manage the resources (postgres database, ec2 instances,...). Using the AWS CLI and the elastic beanstalk CLI, the entire setup can be configurated.

## Installation requirements

To perform these actions, the [AWS CLI](https://aws.amazon.com/cli/) and [eb CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html) are required. Furthermore, make sure to have the AWS authentification and profiles defined for DEV and/or PRD environment.

The elastic beanstalk cli initialization is done using  `eb init`, from which custom adaptations were added (inside the `.ebextensions` and .elasticbeanstalk` folders). When you want to start using elastic beanstalk for the vespawatch, you have to link the initialization with vespawatch application. Execute the command `eb init` in the same folder as the `.ebextensions`, choose `eu-west-1 : EU (Ireland)` and select the vespawatch application when prompted. Say No to using AWS Code Commit.

The tutorial underneath starts from these existing components to create a new environment and provide new deployments.

## Deployment required files

To provide the deployment to AWS using  elastic beanstalk, the following elements are required. First of all, the elastic beanstalk configurations:

- `.elasticbeanstalk`, created by the `eb init` command  containing general config
- `.ebextensions`, containing the django specific elements and steps during deployment (location of the settings file, database migration steps,...

Next, some policies required to setup the application:
- `ec2-trust-policy.json`: assume role of the instance profile, so policies can be linked to ec2 instances.
- `s3-policy.json`: policy to access the vespawatch bucket, which is linked to the ec2 instances running the application
- `s3-tags.json`: tags to indicate the bucket with, required for the admin and cost calculation

## Setup

In general, to create a new environment (dev/prd), following steps are required just a **single time**:

1. Create *key-pair* combination for the EC2 instances
2. Create a *S3 bucket* to store the media files (uploaded photos)
3. Create a custom *instance profile* (role) to attach to the EC2 instances, providing eb policies and S3 bucket access
4. Create the *elastic beanstalk environment*  containing the ec2 instances, database,...

Next, new deployments can be done whenever required using the deployment command:

```
eb deploy --message  "informative message..."
```
### Key-pair combination

It is straightforward to create a new key-pair combination using the AWS Console > EC2 > Key Pairs > `Create Key Pair`.
For development, the key-pair combination is called `LW-INBO-VESPAWATCH-DEV`, in production this is `LW-INBO-VESPAWATCH-PRD`.

Do not forget to put the key-pair combination in the team-folder location.

### S3 Bucket creation

To store the media files (i.e. uploaded images), we use a S3 Bucket. To create the S3 Bucket and add the appropriate tags to it:

```
aws s3api create-bucket --bucket lw-vespawatch --region eu-west-1 --create-bucket-configuration LocationConstraint=eu-west-1 --acl private
aws s3api put-bucket-tagging --bucket lw-vespawatch --tagging file://s3-tags.json
```
For more info, see https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings

Django uses the S3 as a backend using the `django-storages` package, see https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings

### Prepare the ec2 instance profile (role) to access the S3 bucket and manage eb admin

Without providing a `instance-role`, the default is used. However, as we have multiple eb running at inbo, the default instance role (what the EC2 machine is allowed to do) would get mixed permissions attached to it. Hence, we define a custom Instance role and attach the S3 permissions to it:

* create the instance profile for vespawatch
* create a custom role with the S3 access to vespawatch permission
* add the policies from `aws-elasticbeanstalk-ec2-role` (default for EC2s in eb) to the custom role
* attach custom role to the instance profile

```
# create the custom instance profile
aws iam create-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch

# create a custom vespawatch aws-elasticbeanstalk-ec2-role
aws iam create-role --role-name aws-elasticbeanstalk-ec2-role-vespawatch --assume-role-policy-document file://ec2-trust-policy.json --description 'vespawatch application role'

# add the S3 access rule
aws iam put-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-name lw-vespawatch-s3 --policy-document file://s3-policy.json

# add the required elasticbeanstalk policies (taken from aws-elasticbeanstalk-ec2-role)
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkMulticontainerDocker
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkWorkerTier
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::226308051916:policy/AWS-Beanstalk-Volumes

# attach the custom vespawatch aws-elasticbeanstalk-ec2-role
aws iam add-role-to-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch --role-name aws-elasticbeanstalk-ec2-role-vespawatch
```

To get an overview of the instance profiles, check `aws iam list-instance-profiles`

More info on the instance profile creation is provided here:
* https://docs.aws.amazon.com/cli/latest/reference/iam/create-instance-profile.html
* https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/iam-instanceprofile.html
* https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html

**Notice**: As an instance profile can only be linked to a single role, we create a new role with the permissions of the elastic beanstalk default `aws-elasticbeanstalk-ec2-role` role and our own custom policy to access the S3 Bucket.

### create environment

The setup is different in development versus production, as the subnets, security groups and key-pair combination are different. Also on the django side, some configuration settings (settings are contained inside `djangoproject/djangoproject/settings` folder) are different.

First of all, prepare the `settings.py file` depending from the environment working in. If in development, copy the `settings_dev.py` to a `settings.py` file. In production, copy the `settings_prd.py` to a `settings.py` file. This file is referenced inside the `.ebextensions` folder settings to prepare the settings.

For *development*, the environment creation is done with the following command:
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
--vpc.elbsubnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe
--vpc.id vpc-cc8610a8
--vpc.securitygroups sg-ca7ae0b2,sg-4b8f442d
--instance_profile aws-elasticbeanstalk-ec2-role-vespawatch
--keyname LW-INBO-VESPAWATCH-DEV
--tags APPLICATION=VESPAWATCH,ENVIRONMENT=DEV,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
```

For *production*, the environment creation is done with the following command:
```
eb create
--cname vespawatch-prd
--database --database.username $DB_USER --database.password $DB_PWD
--database.size 5
--database.engine postgres
--elb-type classic
--envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD
--region eu-west-1
--vpc
--vpc.dbsubnets subnet-7a763f23,subnet-c4f6ffa1,subnet-9a0a3bed
--vpc.ec2subnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb
--vpc.elbsubnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb
--vpc.id vpc-79d0f71c
--vpc.securitygroups sg-ce6ff5b6,sg-35d5ed51
--instance_profile aws-elasticbeanstalk-ec2-role-vespawatch
--keyname LW-INBO-VESPAWATCH-PRD
--tags APPLICATION=VESPAWATCH,ENVIRONMENT=PRD,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
```

Prompt will provide some additional questions:

```
Enter Environment Name
(default is vespawatch-dev):
```
just accept the default here by enter.

Next:
```
Do you want to associate a public IP address? (Y/n): n
Do you want the load balancer to be public? (Select no for internal) (Y/n): n
```
As these will be handled by the reverse proxy of INBO, this is handles by operations (Bert) and we do not use public ip addresses.

**Notice**: Information on the subnets, vpc and security groups are provided within the console or in the config files of https://github.com/inbo/cloudformation-templates/tree/master/config/vpc

More information on the `eb-create` command, see https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb3-create.html.

## Deploy the django app

When the environment works, the deployment of the application is done by:

```
eb deploy --message "your informatice message"
```

## Bash script for deployment

A small deployment bash script has been prepared to to the entire setup. To execute the setup, make sure your aws profile is set correctly (dev or prd) and execute the script (adapt the capital arguments with more useful names and store these securely)::

```
./setup.sh dev DB_USERNAME DB_PASSWORD KEEPTHISDJANGOKEYSECRET APP_SU_USERNAME APP_SU_PASSWORD
```

Variables:
* `$DB_USER` RDS database user
* `$DB_PWD`   RDS database pwd
* `$DJANGO_SECRET_KEY`   django app secret key
* `$VESPA_SU_NAME`  user name vespawatch applicatie superuser
* `$VESPA_SU_PWD` paswoord vespawatch applicatie superuser

TODO: https://medium.com/@nqbao/how-to-use-aws-ssm-parameter-store-easily-in-python-94fda04fea84

## Backups

- All **code** is under version control and each deployment is stored in a S3 bucket managed by elastic beanstalk
- Backups of the **RDS** are managed on organisation level of INBO.
- Backups of the **media files** in the S3 bucket #TODO

## Setup and configuration info

### ... 

...

### Geo-django

The usage of [geo-django](https://docs.djangoproject.com/en/2.1/ref/contrib/gis/) supporting geographic functionalities requires additional dependencies. On the database side, this requires the Postgis extension to Postgres, which is by default available when using the AWS postgres RDS. 

On the application side, the EC2 servers need to have the `gdal/geos/proj` suite available. Installing `gdal` and `proj` using `yum` is only possible when activating the `epel`  repository. As such, these are included as the first container command in the `01_python.config` file instead of the general list of yum packages in the `02_packages.config`.

## Further info and useful links

* https://realpython.com/deploying-a-django-app-and-postgresql-to-aws-elastic-beanstalk/
* https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-container.html