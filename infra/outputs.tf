# ==============================================================================
# Outputs - デプロイ後に確認すべき情報
# ==============================================================================

# ------------------------------------------------------------------------------
# アクセス URL
# ------------------------------------------------------------------------------
output "frontend_url" {
  description = "Streamlit フロントエンドの URL (port 80)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "backend_url" {
  description = "FastAPI バックエンドの URL (port 8000)"
  value       = "http://${aws_lb.main.dns_name}:8000"
}

output "backend_docs_url" {
  description = "FastAPI Swagger UI の URL"
  value       = "http://${aws_lb.main.dns_name}:8000/docs"
}

output "alb_dns_name" {
  description = "ALB の DNS 名（Route 53 CNAME 等で使用）"
  value       = aws_lb.main.dns_name
}

# ------------------------------------------------------------------------------
# ECR リポジトリ
# ------------------------------------------------------------------------------
output "ecr_backend_repository_url" {
  description = "バックエンドの ECR リポジトリ URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository_url" {
  description = "フロントエンドの ECR リポジトリ URL"
  value       = aws_ecr_repository.frontend.repository_url
}

# ------------------------------------------------------------------------------
# Docker ビルド & プッシュコマンド
# terraform apply 後にこのコマンドを実行してイメージをプッシュする
# ------------------------------------------------------------------------------
output "docker_ecr_login_command" {
  description = "ECR へのログインコマンド"
  value       = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${split("/", aws_ecr_repository.backend.repository_url)[0]}"
}

output "docker_push_backend" {
  description = "バックエンドイメージのビルド & プッシュコマンド"
  value       = <<-EOT
    docker build -t ${aws_ecr_repository.backend.repository_url}:latest ./backend
    docker push ${aws_ecr_repository.backend.repository_url}:latest
  EOT
}

output "docker_push_frontend" {
  description = "フロントエンドイメージのビルド & プッシュコマンド"
  value       = <<-EOT
    docker build -t ${aws_ecr_repository.frontend.repository_url}:latest ./frontend
    docker push ${aws_ecr_repository.frontend.repository_url}:latest
  EOT
}

# ------------------------------------------------------------------------------
# データベース（sensitive: RDS エンドポイントは機密情報として扱う）
# ------------------------------------------------------------------------------
output "rds_endpoint" {
  description = "RDS エンドポイント（ホスト:ポート形式）"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_address" {
  description = "RDS ホスト名（ECS の DB_HOST に設定される値）"
  value       = aws_db_instance.main.address
  sensitive   = true
}

# ------------------------------------------------------------------------------
# ECS
# ------------------------------------------------------------------------------
output "ecs_cluster_name" {
  description = "ECS クラスター名"
  value       = aws_ecs_cluster.main.name
}

# ------------------------------------------------------------------------------
# ネットワーク
# ------------------------------------------------------------------------------
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "パブリックサブネット ID 一覧"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "プライベートサブネット ID 一覧"
  value       = aws_subnet.private[*].id
}
