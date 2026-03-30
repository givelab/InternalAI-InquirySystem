# ==============================================================================
# セキュリティグループ
# 通信フロー: Internet → ALB → ECS(backend/frontend) → RDS
# ==============================================================================

# ------------------------------------------------------------------------------
# ALB セキュリティグループ
# インターネットからの HTTP アクセスと API アクセスを受け付ける
# ------------------------------------------------------------------------------
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Allow HTTP traffic to the Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  # フロントエンド用 (Streamlit)
  ingress {
    description = "HTTP from internet (Streamlit frontend)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # バックエンド API 用 (FastAPI)
  ingress {
    description = "FastAPI backend port from internet"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# ------------------------------------------------------------------------------
# ECS バックエンドセキュリティグループ
# ALB からのトラフィックのみ port 8000 で受け付ける
# ------------------------------------------------------------------------------
resource "aws_security_group" "ecs_backend" {
  name        = "${var.project_name}-ecs-backend-sg"
  description = "Allow traffic to FastAPI backend only from ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "FastAPI port from ALB only"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow all outbound (ECR pull, OpenAI API, RDS, etc.)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-backend-sg"
  }
}

# ------------------------------------------------------------------------------
# ECS フロントエンドセキュリティグループ
# ALB からのトラフィックのみ port 8501 で受け付ける
# ------------------------------------------------------------------------------
resource "aws_security_group" "ecs_frontend" {
  name        = "${var.project_name}-ecs-frontend-sg"
  description = "Allow traffic to Streamlit frontend only from ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Streamlit port from ALB only"
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow all outbound (backend API access, ECR pull, etc.)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-frontend-sg"
  }
}

# ------------------------------------------------------------------------------
# RDS セキュリティグループ
# ECS バックエンドからのトラフィックのみ port 5432 で受け付ける
# ------------------------------------------------------------------------------
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Allow PostgreSQL access only from ECS backend"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from ECS backend only"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}
