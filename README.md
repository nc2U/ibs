[![Build](https://github.com/nc2U/ibs/actions/workflows/django_prod.yml/badge.svg)](https://github.com/nc2U/ibs/actions)
[![Build](https://github.com/nc2U/ibs/actions/workflows/vue_prod.yml/badge.svg)](https://github.com/nc2U/ibs/actions)
![License](https://img.shields.io/github/license/nc2U/ibs)
![Last Commit](https://img.shields.io/github/last-commit/nc2U/ibs)
![Issues](https://img.shields.io/github/issues/nc2U/ibs)
![Stars](https://img.shields.io/github/stars/nc2U/ibs)
![Forks](https://img.shields.io/github/forks/nc2U/ibs)

# Django 5.2 + Vue3 + Svelte using Nginx + MariaDB or PostgreSQL (deploy as Docker or Kubernetes)

## Deploy Using Docker

#### Requirement in your system

- docker
- docker-compose
- node (with pnpm)

### Usage

#### 1. Clone this Repository

```bash
git clone https://github.com/nc2U/ibs
cd ibs
```

#### 2. Copy docker-compose.yml

```bash
cd deploy
cp docker-compose.yml.tmpl docker-compose.yml
```

#### 3. Write environments in docker-compose.yml

Check what must be defined in docker-compose.yml file.

- required:
    - POSTGRES_DB
    - POSTGRES_USER
    - POSTGRES_PASSWORD
    - MYSQL_DATABASE
    - MYSQL_USER
    - MYSQL_PASSWORD
    - MYSQL_ROOT_PASSWORD
    - DATABASE_TYPE
    - DATABASE_NAME
    - DATABASE_USER
    - DATABASE_PASSWORD
    - DOMAIN_NAME
    - EMAIL_HOST
    - EMAIL_PORT
    - EMAIL_HOST_USER
    - EMAIL_HOST_PASSWORD
    - DEFAULT_FROM_EMAIL
    - DJANGO_SETTINGS_MODULE

Enter the actual data for your environment as described in the following items.
If you use a database image such as postgresql or mariadb with Docker, be sure to use the default port.

- postgres:
    - POSTGRES_DB: my-db-name # **postgresql database information**
    - POSTGRES_USER: my-db-user # **postgresql database information**
    - POSTGRES_PASSWORD: my-db-password # **postgresql database information**

- master:
    - MYSQL_DATABASE: my-db-name # **mysql database information**
    - MYSQL_USER: my-db-user # **mysql database information**
    - MYSQL_PASSWORD: my-db-password # **mysql database information**
    - MYSQL_ROOT_PASSWORD: my-db-root-password # **mysql database information**
    - TZ: Asia/Seoul # **mysql database information**

- web:
    - DATABASE_TYPE: mariadb # **mariadb | postgres, default = mariadb, db to use**
    - DATABASE_NAME: my-db-name # **mysql database information**
    - DATABASE_USER: my-db-user # **mysql database information**
    - DATABASE_PASSWORD: my-db-password # **mysql database information**
    - DOMAIN_NAME: my-domain-name # **https://my-domain.com/**
    - EMAIL_HOST: **your-smtp-server.com**
    - EMAIL_PORT: 588 # **default is 587**
    - EMAIL_HOST_USER: **your-access-id-or-email**
    - EMAIL_HOST_PASSWORD: **your-access-password**
    - DEFAULT_FROM_EMAIL: **your-email@example.com**
    - DJANGO_SETTINGS_MODULE: app.settings # **django settings mode**

#### 4. Build & Run Docker Compose

#### Build and run

```bash
docker-compose up -d --build
```

#### 5. Migrate & Basic Settings

#### Migrations & Migrate settings (After build to db & web)

The commands below sequentially run the `python manage.py makemigrations` and `python manage.py migrate` commands.

```bash
docker-compose exec web sh migrate.sh
```

#### Static file Setting

```bash
docker-compose exec web python manage.py collectstatic
```

※ Place your Django project in the **django** directory and develop it.

#### Vue (Single Page Application) Development

```bash
cd ..
cd app/vue3
pnpm i    # npm i (or) yarn
```

Vue application development -> node dev server on.

```bash
pnpm dev    # npm run dev (or) yarn dev
```

or Vue application deploy -> node build

```bash
pnpm build    # npm run build (or) yarn build
```

#### Svelte (Single Page Application) Development

```bash
cd ..
cd app/svelte
pnpm i      # npm i (or) yarn
```

Svelte application development -> node dev server on.

```bash
pnpm dev    # npm run dev (or) yarn dev
```

or Svelte application deploy -> node build

```bash
pnpm build # npm run build (or) yarn build
```

## Or Deploy Using Kubernetes

#### Requirement

- Kubernetes cluster
- Helm
- CI/CD server with helm installed
- NFS Storage server(ip)
- domain(to deploy)
- GitHub account(for using GitHub Actions)
- Docker hub account
- Slack incoming url

### Usage

#### 1. Preparation

###### Kubernetes cluster

Configure a Kubernetes cluster by setting up the required number of nodes.

##### CI/CD server

The ci/cd server uses the master node of the Kubernetes cluster or a separate server or PC.

If you use the master node in the cluster as a ci/cd server, set up external access through ssh and install helm on the
master node.

If you are using a server or PC outside the cluster, configure it to connect via ssh from outside, install helm, and
then copy and configure the kubeconfig file to the user's home directory to access and control the master node.

Check the IP or domain that can access the ci/cd server.

##### NFS storage server

For the nfs storage server, it is recommended to prepare a separate server if a large amount of data will be used in the
future, but you can also use the cluster's master node or ci/cd server.

Install the necessary packages according to the operating system on the server to be used as a storage server, run it as
an NFS server, and connect it to the Kubernetes cluster nodes.

Also, enable connection via ssh and check the accessible IP or domain.

##### Domain & DNS setting

Secure the domain to be used for this project and connect each cluster node to the domain.

##### installing the cert-manager Chart

Full installation instructions, including details on how to configure extra functionality in cert-manager can be found
in the [installation docs](https://cert-manager.io/docs/releases/).

Before installing the chart, you must first install the cert-manager CustomResourceDefinition resources. This is
performed in a separate step to allow you to easily uninstall and reinstall cert-manager without deleting your installed
custom resources.

```bash
$ kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.18.2/cert-manager.crds.yaml
```

To install the chart with the release name `cert-manager`:

```bash
## Add the Jetstack Helm repository

$ helm repo add jetstack https://charts.jetstack.io --force-update

## Install the cert-manager helm chart

$ helm install cert-manager --namespace cert-manager --version v1.18.2 jetstack/cert-manager --create-namespace
```

##### installing the ingress-nginx Chart

Get repo info

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
```

install Chart

```bash
helm install [RELEASE_NAME] -n ingress-nginx ingress-nginx/ingress-nginx --create-namespace
```

##### GitHub & DockerHub account, Slack incoming url

Use an existing GitHub account or create a new one and fork this project.

Afterward, go to the Settings > Secrets and variables > Actions menu and click the 'New repository secret' button to
create Repository secrets with the keys and values below.

- CICD_HOST: # cicd server host(ip or domain)
- CICD_PASS: # cicd server user password
- CICD_PATH: # cicd helm chart & volume path
- CICD_USER: # cicd server user
- DATABASE_PASS: # root & db user password
- DATABASE_USER: # db & db user name
- DOCKERHUB_TOKEN: # docker hub user password (If you manage your images in your own Docker hub)
- DOCKERHUB_USER: # docker hub user id (If you manage your images in your own Docker hub)
- DOMAIN_HOST: # full address (https://abc.com/ for getting url)
- DOMAIN_NANE: # domain address (for ingress)
- DEFAULT_FROM_EMAIL: # your-email@example.com
- EMAIL_HOST: # your-smtp-server.com
- EMAIL_HOST_PASSWORD: # your-access-password
- EMAIL_HOST_USER: # your-access-id-or-email
- NFS_HOST:  # nfs storage server host(ip or domain)
- NFS_PASS:  # nfs storage server user password
- NFS_PATH:  # nfs storage server path (absolute path)
- NFS_USER:  # nfs storage server user
- SLACK_INCOMING_URL: # slack incoming url

#### 2. Deploy

Go to the action tab in the GitHub repository.

Click 'Show more workflows...' at the bottom of all workflows, click `_initial [Prod Step1]`, and then use the
Kubernetes `watch` command on the cicd server to check whether the relevant PODs are created and operating normally.

When all database pods operate normally,
Click `_initial [Prod Step2]` at the bottom of all workflows in the action tab.

#### 3. Or Manually Deploy

```bash
cd deploy/helm

if ! helm repo list | grep -q 'nfs-subdir-external-provisioner'; then
  helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner
fi
if ! helm status nfs-subdir-external-provisioner -n kube-system >/dev/null 2>&1; then
  helm upgrade --install nfs-subdir-external-provisioner \
    nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
      -n kube-system \
      --set nfs.server={ CICD_HOST} \
      --set nfs.path=/mnt/nfs-subdir-external-provisioner
fi

kubectl apply -f deploy/kubectl/class-roles; cd deploy/helm

helm upgrade {DATABASE_USER} . -f ./values.yaml \
  --install -n ibs-prod --create-namespace --history-max 5 --wait --timeout 10m \
  --set global.dbPassword={DATABASE_PASS} \
  --set global.cicdPath={CICD_PATH} \
  --set global.cicdServerHost={CICD_HOST} \
  --set global.nfsPath={NFS_PATH} \
  --set global.nfsServerHost={NFS_HOST} \
  --set global.domainHost={DOMAIN_HOST} \
  --set global.emailHost={EMAIL_HOST} \
  --set global.emailHostUser={EMAIL_HOST_USER} \
  --set-string global.emailHostPassword='{EMAIL_HOST_PASSWORD}' \
  --set global.defaultFromEmail={EMAIL_DEFAULT_FROM} \
  --set postgres.auth.postgresPassword={DATABASE_PASS} \
  --set postgres.auth.password={DATABASE_PASS} \
  --set postgres.auth.replicationPassword={DATABASE_PASS} \
  --set 'nginx.ingress.hosts[0].host'={DOMAIN_NAME} \
  --set 'nginx.ingress.hosts[0].paths[0].path'=/ \
  --set 'nginx.ingress.hosts[0].paths[0].pathType'=Prefix \
  --set 'nginx.ingress.hosts[1].paths[0].path'=/ \
  --set 'nginx.ingress.hosts[1].paths[0].pathType'=Prefix \
  --set 'nginx.ingress.hosts[2].paths[0].path'=/ \
  --set 'nginx.ingress.hosts[2].paths[0].pathType'=Prefix \
  --set 'nginx.ingress.hosts[3].paths[0].path'=/ \
  --set 'nginx.ingress.hosts[3].paths[0].pathType'=Prefix \
  --set 'nginx.ingress.tls[0].hosts[0]'={DOMAIN_NAME} \
  --set 'nginx.ingress.tls[0].secretName'=web-devbox-kr-cert # Replace {TEXT} part with the corresponding setting value
```

#### 4. if you deploy the release manually: Migrate & Basic Settings

If all pods are running normally, run the following procedure.
The commands below sequentially run the `python manage.py makemigrations` and `python manage.py migrate` commands.

```bash
kubectl exec -it {web-pod} sh migrate.sh  # Replace {web-pod} with the actual pod name.
```

#### Static file Setting

```bash
kubectl exec -it {web-pod} python manage.py collectstatic  # Replace {web-pod} with the actual pod name.
```

※ Place your Django project in the **django** directory and develop it.

#### Vue (Single Page Application) Development

```bash
cd ..
cd app/vue3
pnpm i    # npm i (or) yarn
```

Vue application development -> node dev server on.

```bash
pnpm dev    # npm run dev (or) yarn dev
```

or Vue application deploy -> node build

```bash
pnpm build    # npm run build (or) yarn build
```

#### Svelte (Single Page Application) Development

```bash
cd ..
cd app/svelte
pnpm i      # npm i (or) yarn
```

Svelte application development -> node dev server on.

```bash
pnpm dev    # npm run dev (or) yarn dev
```

or Svelte application deploy -> node build

```bash
pnpm build # npm run build (or) yarn build
```

#### Reference

- [Python](https://www.python.org)
- [Docker](https://www.docker.com)
- [Docker compose](https://docs.docker.com/compose)
- [Kubernetes](https://kubernetes.io/docs/home/)
- [Helm](https://helm.sh/docs/)
- [Nginx](https://www.nginx.com/)
- [MariaDB](https://mariadb.org)
- [PostgreSQL](https://www.postgresql.org/)
- [Django](https://www.djangoproject.com)
- [Django Rest Framework](https://www.django-rest-framework.org/)
- [Node](https://nodejs.org/ko/)
- [Pnpm](https://pnpm.io/)
