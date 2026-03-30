# ==============================================================================
# ECS Cluster
# ==============================================================================
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# ==============================================================================
# CloudWatch Logs（コンテナログの保存先）
# ==============================================================================
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}/backend"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-backend-logs"
  }
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project_name}/frontend"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-frontend-logs"
  }
}

# ==============================================================================
# SSM Parameter Store（シークレット管理）
# ECS タスク定義から `secrets` キーで参照し、コンテナに環境変数として注入する
# ==============================================================================
resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project_name}/${var.environment}/db_password"
  type  = "SecureString"
  value = var.db_password

  tags = {
    Name = "${var.project_name}-db-password"
  }
}

resource "aws_ssm_parameter" "openai_api_key" {
  name  = "/${var.project_name}/${var.environment}/openai_api_key"
  type  = "SecureString"
  value = var.openai_api_key != "" ? var.openai_api_key : "placeholder-replace-me"

  tags = {
    Name = "${var.project_name}-openai-api-key"
  }
}

# Gemini API Key（OpenAI の代替として使用する場合）
resource "aws_ssm_parameter" "gemini_api_key" {
  name  = "/${var.project_name}/${var.environment}/gemini_api_key"
  type  = "SecureString"
  value = var.gemini_api_key != "" ? var.gemini_api_key : "placeholder-replace-me"

  tags = {
    Name = "${var.project_name}-gemini-api-key"
  }
}

# ==============================================================================
# IAM ロール
# ==============================================================================

# --- ECS タスク実行ロール ---
# ECR からのイメージ pull と CloudWatch Logs への書き込みに必要
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${var.project_name}-ecs-task-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# SSM Parameter Store の読み取りを許可するポリシー
resource "aws_iam_policy" "ssm_read" {
  name        = "${var.project_name}-ssm-read-policy"
  description = "Allow ECS task execution role to read secrets from SSM Parameter Store"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameters",
        "ssm:GetParameter",
        "kms:Decrypt"
      ]
      Resource = [
        aws_ssm_parameter.db_password.arn,
        aws_ssm_parameter.openai_api_key.arn,
        aws_ssm_parameter.gemini_api_key.arn,
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_read" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.ssm_read.arn
}

# --- ECS タスクロール ---
# コンテナ内アプリケーションが AWS サービスを呼び出す際に使用するロール
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${var.project_name}-ecs-task-role"
  }
}

# ==============================================================================
# ECS タスク定義 - バックエンド (FastAPI)
# ==============================================================================
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = var.backend_image != "" ? var.backend_image : "${aws_ecr_repository.backend.repository_url}:latest"
      essential = true

      portMappings = [{ containerPort = 8000, protocol = "tcp" }]

      # 非機密の環境変数はここに直接記述
      environment = [
        { name = "DB_HOST", value = aws_db_instance.main.address },
        { name = "DB_PORT", value = tostring(aws_db_instance.main.port) },
        { name = "DB_NAME", value = var.db_name },
        { name = "DB_USER", value = var.db_username },
        { name = "DB_POOL_SIZE", value = "5" },
        { name = "DB_POOL_TIMEOUT", value = "10" },
        { name = "LOG_LEVEL", value = "INFO" },
      ]

      # 機密情報は SSM Parameter Store から取得して環境変数に注入
      secrets = [
        { name = "DB_PASSWORD", valueFrom = aws_ssm_parameter.db_password.arn },
        { name = "OPENAI_API_KEY", valueFrom = aws_ssm_parameter.openai_api_key.arn },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health-check || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60 # DB 接続確立まで待機
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-backend-task"
  }
}

# ==============================================================================
# ECS タスク定義 - フロントエンド (Streamlit)
# ==============================================================================
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project_name}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = var.frontend_image != "" ? var.frontend_image : "${aws_ecr_repository.frontend.repository_url}:latest"
      essential = true

      portMappings = [{ containerPort = 8501, protocol = "tcp" }]

      # API_BASE_URL: ALB のポート 8000 経由でバックエンドへアクセス
      environment = [
        { name = "API_BASE_URL", value = "http://${aws_lb.main.dns_name}:8000" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-frontend-task"
  }
}

# ==============================================================================
# ECS サービス - バックエンド
# ==============================================================================
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-backend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_backend.id]
    assign_public_ip = false # NAT GW 経由でインターネットへアクセス
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  depends_on = [
    aws_lb_listener.backend,
    aws_iam_role_policy_attachment.ecs_task_execution,
  ]

  tags = {
    Name = "${var.project_name}-backend-service"
  }
}

# ==============================================================================
# ECS サービス - フロントエンド
# ==============================================================================
resource "aws_ecs_service" "frontend" {
  name            = "${var.project_name}-frontend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_frontend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 8501
  }

  depends_on = [
    aws_lb_listener.frontend,
    aws_iam_role_policy_attachment.ecs_task_execution,
  ]

  tags = {
    Name = "${var.project_name}-frontend-service"
  }
}
