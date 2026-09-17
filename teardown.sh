#!/bin/bash
set -e

REGION="us-east-1"
BUCKET_NAME="instabox-app-emilio-maciel"
DB_IDENTIFIER="instabox-db"
SECRET_NAME="instabox/rds/credentials"

echo "=== INICIANDO TEARDOWN DE INSTABOX ==="

# 1. Vaciar y eliminar Bucket S3
echo "[1/4] Vaciando y eliminando bucket S3: $BUCKET_NAME..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    aws s3 rm "s3://$BUCKET_NAME" --recursive
    aws s3api delete-bucket --bucket "$BUCKET_NAME" --region "$REGION"
    echo "Bucket S3 eliminado."
else
    echo "El bucket S3 no existe o ya fue eliminado."
fi

# 2. Eliminar Instancia RDS (sin snapshot final)
echo "[2/4] Eliminando instancia RDS: $DB_IDENTIFIER..."
if aws rds describe-db-instances --db-instance-identifier "$DB_IDENTIFIER" --region "$REGION" 2>/dev/null; then
    aws rds delete-db-instance \
        --db-instance-identifier "$DB_IDENTIFIER" \
        --skip-final-snapshot \
        --delete-automated-backups \
        --region "$REGION" > /dev/null
    echo "Solicitud de eliminación de RDS enviada (tomará unos minutos en desaparecer)."
else
    echo "La instancia RDS no existe o ya fue eliminada."
fi

# 3. Eliminar Secreto en Secrets Manager
echo "[3/4] Eliminando secreto: $SECRET_NAME..."
if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$REGION" 2>/dev/null; then
    aws secretsmanager delete-secret \
        --secret-id "$SECRET_NAME" \
        --force-delete-without-recovery \
        --region "$REGION" > /dev/null
    echo "Secreto eliminado permanentemente."
else
    echo "El secreto no existe o ya fue eliminado."
fi

# 4. Terminar Instancia EC2
echo "[4/4] Buscando y terminando instancia EC2 con tag instabox-ec2..."
INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=instabox-ec2" "Name=instance-state-name,Values=running,pending,stopped" \
    --query "Reservations[].Instances[].InstanceId" \
    --output text --region "$REGION")

if [ -n "$INSTANCE_ID" ]; then
    aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region "$REGION" > /dev/null
    echo "Instancia EC2 $INSTANCE_ID en proceso de terminación."
else
    echo "No se encontró ninguna instancia EC2 activa llamada instabox-ec2."
fi

echo "=== TEARDOWN COMPLETADO ==="