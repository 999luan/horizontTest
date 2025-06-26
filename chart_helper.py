import json
from typing import Dict, Any, Optional

def create_comparison_chart(initial_value: float, years: int = 5, products: Optional[Dict[str, Dict[str, float]]] = None) -> str:
    """
    Cria um JSON formatado para gráfico de comparação de investimentos.
    
    Args:
        initial_value: Valor inicial do investimento
        years: Número de anos para projeção
        products: Dicionário com produtos e suas taxas. Se None, usa produtos padrão.
    
    Returns:
        String JSON formatada entre tags [GRAFICO_DADOS]
    """
    if products is None:
        products = {
            "Poupança": {"rate": 7.75, "yearlyMultiplier": 1.0775},
            "CDI": {"rate": 10.88, "yearlyMultiplier": 1.1088},
            "Horizont Smart": {"rate": 15.39, "monthlyRate": 0.012, "yearlyMultiplier": 1.1539},
            "Horizont Trend": {"rate": 19.37, "yearlyMultiplier": 1.1937}
        }
    
    chart_data = {
        "type": "comparison",
        "title": "Comparativo de Investimentos",
        "years": years,
        "initialValue": initial_value,
        "products": products
    }
    
    return f"[GRAFICO_DADOS]\n{json.dumps(chart_data, indent=2, ensure_ascii=False)}\n[/GRAFICO_DADOS]"

def create_product_chart(product_name: str, initial_value: float, years: int = 5, monthly_rate: Optional[float] = None, yearly_rate: Optional[float] = None) -> str:
    """
    Cria um JSON formatado para gráfico de um produto específico.
    
    Args:
        product_name: Nome do produto
        initial_value: Valor inicial do investimento
        years: Número de anos para projeção
        monthly_rate: Taxa mensal (opcional)
        yearly_rate: Taxa anual (opcional)
    
    Returns:
        String JSON formatada entre tags [GRAFICO_DADOS]
    """
    if monthly_rate:
        yearly_multiplier = (1 + monthly_rate) ** 12
        rate = monthly_rate * 100 * 12
    elif yearly_rate:
        yearly_multiplier = 1 + (yearly_rate / 100)
        rate = yearly_rate
    else:
        raise ValueError("Deve fornecer taxa mensal ou anual")
    
    products = {
        product_name: {
            "rate": rate,
            "yearlyMultiplier": yearly_multiplier
        }
    }
    
    if monthly_rate:
        products[product_name]["monthlyRate"] = monthly_rate
    
    chart_data = {
        "type": "single",
        "title": f"Projeção - {product_name}",
        "years": years,
        "initialValue": initial_value,
        "products": products
    }
    
    return f"[GRAFICO_DADOS]\n{json.dumps(chart_data, indent=2, ensure_ascii=False)}\n[/GRAFICO_DADOS]"

def format_chart_example() -> str:
    """
    Retorna um exemplo formatado de como gerar um gráfico.
    """
    return create_comparison_chart(500000, 5) 