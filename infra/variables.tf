variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "internal-ai"
}

variable "environment" {
  description = "Environment name (e.g. production, staging)"
  type        = string
  default     = "production"
}

# -----------------------------------------------
# Network
# -----------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "availability_zones" {
  description = "Availability zones to use (must match subnet count)"
  type        = list(string)
  default     = ["ap-northeast-1a", "ap-northeast-1c"]
}

# -----------------------------------------------
# RDS
# -----------------------------------------------
variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "chat_app"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "PostgreSQL master password (use tfvars or environment variable)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

# -----------------------------------------------
# ECS Task sizing
# -----------------------------------------------
variable "backend_cpu" {
  description = "vCPU units for the backend Fargate task (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "backend_memory" {
  description = "Memory (MiB) for the backend Fargate task"
  type        = number
  default     = 512
}

variable "frontend_cpu" {
  description = "vCPU units for the frontend Fargate task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory (MiB) for the frontend Fargate task"
  type        = number
  default     = 512
}

variable "backend_desired_count" {
  description = "Desired number of running backend tasks"
  type        = number
  default     = 1
}

variable "frontend_desired_count" {
  description = "Desired number of running frontend tasks"
  type        = number
  default     = 1
}

# -----------------------------------------------
# Application secrets
# -----------------------------------------------
variable "openai_api_key" {
  description = "OpenAI API key injected into the backend container via SSM"
  type        = string
  sensitive   = true
  default     = ""
}

variable "gemini_api_key" {
  description = "Gemini API key (alternative to OpenAI)"
  type        = string
  sensitive   = true
  default     = ""
}

# -----------------------------------------------
# Container images
# When left empty, the ECR repository URL + :latest is used automatically.
# Override after the first `docker push` if you want a specific tag.
# -----------------------------------------------
variable "backend_image" {
  description = "Full ECR image URI for the backend (e.g. 123456789.dkr.ecr.ap-northeast-1.amazonaws.com/internal-ai/backend:v1.0)"
  type        = string
  default     = ""
}

variable "frontend_image" {
  description = "Full ECR image URI for the frontend"
  type        = string
  default     = ""
}
