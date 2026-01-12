"""Utilitário para retry com backoff exponencial."""
from __future__ import annotations

import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
    retryable_status_codes: tuple[int, ...] = (500, 502, 503, 504),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator para retry com backoff exponencial.
    
    Args:
        max_retries: Número máximo de tentativas
        base_delay: Delay base em segundos
        max_delay: Delay máximo em segundos
        exponential_base: Base para cálculo exponencial
        retryable_exceptions: Tupla de exceções que devem ser retentadas
        retryable_status_codes: Códigos HTTP que devem ser retentados
    
    Returns:
        Função decorada com retry automático
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Verificar se é um erro HTTP retentável
                    is_retryable = False
                    error_str = str(e)
                    
                    # Verificar códigos de status HTTP
                    for status_code in retryable_status_codes:
                        if f"HttpError {status_code}" in error_str or f"{status_code}" in error_str:
                            is_retryable = True
                            break
                    
                    # Verificar se é uma exceção retentável
                    if not is_retryable:
                        for exc_type in retryable_exceptions:
                            if isinstance(e, exc_type):
                                # Apenas retry para erros de conexão/timeout
                                if any(keyword in error_str.lower() for keyword in [
                                    "timeout", "connection", "unavailable", "temporarily"
                                ]):
                                    is_retryable = True
                                    break
                    
                    if not is_retryable or attempt == max_retries:
                        logger.error(
                            f"Falha definitiva em {func.__name__} após {attempt + 1} tentativa(s): {e}"
                        )
                        raise
                    
                    # Calcular delay com backoff exponencial
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        f"Tentativa {attempt + 1}/{max_retries + 1} falhou para {func.__name__}. "
                        f"Erro: {e}. Retentando em {delay:.1f}s..."
                    )
                    
                    time.sleep(delay)
            
            # Não deveria chegar aqui, mas por segurança
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Retry exausto para {func.__name__}")
        
        return wrapper
    return decorator