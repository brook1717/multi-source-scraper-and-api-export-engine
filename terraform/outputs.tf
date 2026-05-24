output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "api_url" {
  description = "Public URL of the FastAPI service"
  value       = "http://${aws_lb.api.dns_name}"
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}
