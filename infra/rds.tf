# ==============================================================================
# RDS for PostgreSQL
# ==============================================================================

# RDS を配置するサブネットグループ（プライベートサブネット 2 AZ）
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# パラメータグループ（接続ログを有効化）
resource "aws_db_parameter_group" "main" {
  name   = "${var.project_name}-db-pg"
  family = "postgres15"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  tags = {
    Name = "${var.project_name}-db-pg"
  }
}

# RDS PostgreSQL インスタンス（シングル AZ / コスト最適化）
resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-db"
  engine         = "postgres"
  engine_version = "15.7"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.main.name

  # ストレージ（gp2, 自動拡張あり）
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  # シングル AZ（コスト削減）
  multi_az = false

  # バックアップ
  backup_retention_period  = 7
  backup_window            = "03:00-04:00"
  maintenance_window       = "Mon:04:00-Mon:05:00"
  delete_automated_backups = true

  # 削除保護（開発中は false）
  deletion_protection = false
  skip_final_snapshot = true

  # Performance Insights（7日間は無料）
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  tags = {
    Name = "${var.project_name}-db"
  }
}
