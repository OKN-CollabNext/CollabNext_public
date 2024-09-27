# Change these values to the ones used to create the App Service.
SUBSCRIPTION=0bdb7994-618e-43ab-9dc4-e5510263d104
RESOURCE_GROUP_NAME='collabnext_alpha'
APP_SERVICE_NAME='collabnext'

az login

az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP_NAME \
    --name $APP_SERVICE_NAME \
    --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true
sleep 5

az webapp config set --resource-group $RESOURCE_GROUP_NAME --name $APP_SERVICE_NAME --startup-file startup.txt

sleep 5

rm -rf backend/build
rm -rf backend/.venv
rm -rf backend/__pycache__
cd frontend
npm install --legacy-peer-deps
npm install @memgraph/orb
npm run build
mkdir ../backend/build
cp -r build/* ../backend/build
cd ..

zip -r collab.zip backend -x '.??*'

sleep 5
az webapp deploy \
    --name $APP_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --src-path collab.zip