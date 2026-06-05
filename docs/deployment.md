## Deployment Steps

### 1. Create a Resource Group

A resource group holds all the Azure resources for this project. Deleting the group later removes everything in one command.

```bash
az group create --name nairafx-rg --location uksouth
```

### 2. Create an Azure Container Registry

ACR stores Docker images privately within Azure. The Basic SKU is sufficient for small projects.

```bash
az acr create \
  --resource-group nairafx-rg \
  --name <your-unique-registry-name> \
  --sku Basic \
  --admin-enabled true
```

The registry name must be globally unique across Azure. Try `nairafxregistry<yourinitials><year>`.

### 3. Get Registry Credentials

The Container Instance needs credentials to pull from the private registry.

```bash
az acr credential show --name <your-unique-registry-name>
```

Note the username and password from the output.

### 4. Build and Push the Docker Image

```bash
# Log Docker in to the registry
az acr login --name <your-unique-registry-name>

# Build the image with the registry URL as the tag
docker build -t <your-unique-registry-name>.azurecr.io/nairafx-app:v1 ./app

# Push the image
docker push <your-unique-registry-name>.azurecr.io/nairafx-app:v1
```

### 5. Deploy to Azure Container Instances

```bash
az container create \
  --resource-group nairafx-rg \
  --name nairafx-app \
  --image <your-unique-registry-name>.azurecr.io/nairafx-app:v1 \
  --registry-login-server <your-unique-registry-name>.azurecr.io \
  --registry-username <username from step 3> \
  --registry-password <password from step 3> \
  --dns-name-label <unique-dns-label> \
  --ports 5000 \
  --environment-variables APP_NAME=NairaFX REFRESH_MINUTES=15
```

### 6. Get the Public URL

```bash
az container show \
  --resource-group nairafx-rg \
  --name nairafx-app \
  --query ipAddress.fqdn
```

Visit `http://<output-fqdn>:5000` in your browser.

## Troubleshooting

### Container fails to start

Check the logs:
```bash
az container logs --resource-group nairafx-rg --name nairafx-app
```

### Image pull errors

Verify the registry credentials are correct and the image was pushed successfully:
```bash
az acr repository list --name <your-unique-registry-name>
```

## Tearing Down

To remove all Azure resources for this project:

```bash
az group delete --name nairafx-rg --yes --no-wait
```

This deletes the resource group and everything inside it.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| APP_NAME | NairaFX | Display name shown in the UI |
| REFRESH_MINUTES | 15 | How often the cache refreshes from the upstream API |
