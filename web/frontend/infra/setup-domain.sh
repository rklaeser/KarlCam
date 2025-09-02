#!/bin/bash
# Set up custom domain for KarlCam frontend

set -e

PROJECT_ID="karlcam"
REGION="us-central1"
DOMAIN="karlcam.xyz"

echo "🌐 Setting up custom domain for KarlCam"
echo "======================================"

# Set project
gcloud config set project ${PROJECT_ID}

echo "📋 Prerequisites checklist:"
echo "  ✅ Domain registered and DNS managed by you"
echo "  ✅ Frontend service deployed (karlcam-frontend)"
echo ""

# Get the current Cloud Run service URL
FRONTEND_URL=$(gcloud run services describe karlcam-frontend --region ${REGION} --format 'value(status.url)' 2>/dev/null)
if [ -z "$FRONTEND_URL" ]; then
    echo "❌ Frontend service not found. Run ./deploy.sh first."
    exit 1
fi

echo "🔍 Current frontend URL: ${FRONTEND_URL}"
echo ""

# Map custom domain to Cloud Run service
echo "🔗 Mapping ${DOMAIN} to karlcam-frontend service..."
gcloud beta run domain-mappings create \
    --service karlcam-frontend \
    --domain ${DOMAIN} \
    --region ${REGION}

# Get the required DNS records
echo ""
echo "📝 Required DNS Records:"
echo "========================"
echo ""
echo "Add these records to your ${DOMAIN} DNS configuration:"
echo ""

# Get the domain mapping details
gcloud beta run domain-mappings describe ${DOMAIN} --region ${REGION} --format="table(
    status.conditions[].type:label=CONDITION,
    status.conditions[].status:label=STATUS,
    status.resourceRecords[].name:label=NAME,
    status.resourceRecords[].rrdata:label=VALUE,
    status.resourceRecords[].type:label=TYPE
)"

echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Add the DNS records shown above to your domain registrar"
echo "2. Wait for DNS propagation (up to 24 hours)"
echo "3. Verify SSL certificate is issued automatically"
echo "4. Test: curl -I https://${DOMAIN}"
echo ""
echo "🔒 HTTPS will be automatically enabled with Google-managed SSL certificate"
echo ""
echo "📊 Monitor status:"
echo "  gcloud beta run domain-mappings describe ${DOMAIN} --region ${REGION}"
echo ""

# Optional: Set up www redirect
read -p "🤔 Do you want to set up www.${DOMAIN} redirect? (y/N): " setup_www
if [[ $setup_www =~ ^[Yy]$ ]]; then
    echo "🔗 Setting up www.${DOMAIN} redirect..."
    gcloud beta run domain-mappings create \
        --service karlcam-frontend \
        --domain www.${DOMAIN} \
        --region ${REGION}
    
    echo "✅ Don't forget to add DNS records for www.${DOMAIN} too!"
fi

echo ""
echo "✅ Domain mapping setup complete!"
echo ""
echo "⚠️  Important: DNS changes can take up to 24 hours to propagate globally"
echo ""