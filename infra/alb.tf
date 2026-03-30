# ==============================================================================
# Application Load Balancer
# ポート 80  → Streamlit フロントエンド (8501)
# ポート 8000 → FastAPI バックエンド (8000)
# ==============================================================================

resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# ------------------------------------------------------------------------------
# ターゲットグループ
# ------------------------------------------------------------------------------

# バックエンド (FastAPI port 8000)
resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip" # Fargate は ip タイプを使用

  health_check {
    enabled             = true
    path                = "/health-check" # FastAPI の /health-check エンドポイント
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "${var.project_name}-backend-tg"
  }
}

# フロントエンド (Streamlit port 8501)
resource "aws_lb_target_group" "frontend" {
  name        = "${var.project_name}-frontend-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/_stcore/health" # Streamlit 組み込みのヘルスチェックパス
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "${var.project_name}-frontend-tg"
  }
}

# ------------------------------------------------------------------------------
# リスナー
# ------------------------------------------------------------------------------

# ポート 80 → フロントエンド (Streamlit)
resource "aws_lb_listener" "frontend" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# ポート 8000 → バックエンド (FastAPI)
resource "aws_lb_listener" "backend" {
  load_balancer_arn = aws_lb.main.arn
  port              = 8000
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
