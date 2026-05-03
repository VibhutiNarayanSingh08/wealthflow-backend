"""
Portfolio Connector - Connect your actual purchased holdings
Supports multiple methods: API integration, CSV import, manual entry
"""

import json
import csv
import os
from typing import Dict, List, Optional
from datetime import datetime
import requests

class PortfolioConnector:
    def __init__(self, indstocks_token: str = None):
        self.indstocks_token = indstocks_token or os.getenv('INDSTOCKS_TOKEN')
        self.indstocks_headers = {
            'Authorization': self.indstocks_token,
            'Content-Type': 'application/json'
        }
    
    def connect_indstocks_portfolio(self) -> Dict:
        """
        Method 1: Connect via IndStocks API (if your broker is IndStocks)
        This fetches your actual holdings and positions from IndStocks
        """
        if not self.indstocks_token:
            return {'error': 'IndStocks token required'}
        
        try:
            # Get holdings from IndStocks
            holdings_response = requests.get(
                'https://api.indstocks.com/portfolio/holdings',
                headers=self.indstocks_headers
            )
            
            # Get positions from IndStocks  
            positions_response = requests.get(
                'https://api.indstocks.com/portfolio/positions',
                headers=self.indstocks_headers
            )
            
            portfolio_data = {
                'holdings': holdings_response.json() if holdings_response.status_code == 200 else {},
                'positions': positions_response.json() if positions_response.status_code == 200 else {},
                'source': 'indstocks_api',
                'last_updated': datetime.now().isoformat()
            }
            
            return portfolio_data
            
        except Exception as e:
            return {'error': f'Failed to connect IndStocks: {str(e)}'}
    
    def import_from_csv(self, csv_file_path: str) -> Dict:
        """
        Method 2: Import portfolio from CSV file
        CSV format: symbol,quantity,avg_price,transaction_type,category
        """
        try:
            portfolio = []
            with open(csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    portfolio.append({
                        'symbol': row.get('symbol', '').strip(),
                        'quantity': float(row.get('quantity', 0)),
                        'avg_price': float(row.get('avg_price', 0)),
                        'transaction_type': row.get('transaction_type', 'BUY'),
                        'category': row.get('category', 'stock'),
                        'investment_value': float(row.get('quantity', 0)) * float(row.get('avg_price', 0))
                    })
            
            return {
                'portfolio': portfolio,
                'source': 'csv_import',
                'total_investment': sum(item['investment_value'] for item in portfolio),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Failed to import CSV: {str(e)}'}
    
    def add_manual_holdings(self, holdings_data: List[Dict]) -> Dict:
        """
        Method 3: Manually add holdings
        holdings_data format: [
            {
                'symbol': 'RELIANCE',
                'quantity': 100,
                'avg_price': 2500.50,
                'category': 'stock'
            },
            {
                'scheme_code': '125497',
                'units': 150.5,
                'avg_nav': 180.25,
                'category': 'mutual_fund'
            }
        ]
        """
        try:
            processed_holdings = []
            for holding in holdings_data:
                if holding.get('category') == 'mutual_fund':
                    # Get current NAV for mutual fund
                    current_nav = self._get_current_mf_nav(holding['scheme_code'])
                    processed_holdings.append({
                        **holding,
                        'current_value': holding['units'] * current_nav,
                        'investment_value': holding['units'] * holding['avg_nav'],
                        'returns': holding['units'] * (current_nav - holding['avg_nav'])
                    })
                else:
                    # Get current price for stock
                    current_price = self._get_current_stock_price(holding['symbol'])
                    processed_holdings.append({
                        **holding,
                        'current_value': holding['quantity'] * current_price,
                        'investment_value': holding['quantity'] * holding['avg_price'],
                        'returns': holding['quantity'] * (current_price - holding['avg_price'])
                    })
            
            return {
                'holdings': processed_holdings,
                'source': 'manual_entry',
                'total_investment': sum(item['investment_value'] for item in processed_holdings),
                'total_current_value': sum(item['current_value'] for item in processed_holdings),
                'total_returns': sum(item['returns'] for item in processed_holdings),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Failed to process manual holdings: {str(e)}'}
    
    def _get_current_stock_price(self, symbol: str) -> float:
        """Get current stock price from IndStocks API"""
        try:
            # Convert symbol to IndStocks format (assuming NSE)
            scrip_code = f"NSE_{self._get_scrip_code(symbol)}"
            
            response = requests.get(
                f'https://api.indstocks.com/market/quotes/ltp',
                headers=self.indstocks_headers,
                params={'scrip-codes': scrip_code}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and data.get('data'):
                    return float(data['data'][0].get('ltp', 0))
            
            return 0.0
            
        except:
            return 0.0
    
    def _get_current_mf_nav(self, scheme_code: str) -> float:
        """Get current NAV from mfapi.in"""
        try:
            response = requests.get(f'https://api.mfapi.in/mf/{scheme_code}/latest')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'SUCCESS' and data.get('data'):
                    return float(data['data'][0].get('nav', 0))
            
            return 0.0
            
        except:
            return 0.0
    
    def _get_scrip_code(self, symbol: str) -> str:
        """Convert symbol to scrip code (simplified mapping)"""
        # This is a simplified mapping - in reality, you'd need a comprehensive symbol to scrip code mapping
        symbol_mapping = {
            'RELIANCE': '3045',
            'TCS': '11532',
            'HDFCBANK': '500112',
            'INFY': '500209',
            'ICICIBANK': '532174'
        }
        return symbol_mapping.get(symbol, symbol)
    
    def create_sample_csv_template(self, file_path: str):
        """Create a sample CSV template for portfolio import"""
        sample_data = [
            {'symbol': 'RELIANCE', 'quantity': '50', 'avg_price': '2500', 'transaction_type': 'BUY', 'category': 'stock'},
            {'symbol': 'TCS', 'quantity': '25', 'avg_price': '3500', 'transaction_type': 'BUY', 'category': 'stock'},
            {'scheme_code': '125497', 'quantity': '100', 'avg_price': '180', 'transaction_type': 'BUY', 'category': 'mutual_fund'}
        ]
        
        with open(file_path, 'w', newline='') as file:
            fieldnames = ['symbol', 'quantity', 'avg_price', 'transaction_type', 'category']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_data)
        
        print(f"✅ Sample CSV template created: {file_path}")
    
    def generate_portfolio_summary(self, portfolio_data: Dict) -> str:
        """Generate comprehensive portfolio summary"""
        if 'error' in portfolio_data:
            return f"❌ Error: {portfolio_data['error']}"
        
        summary = f"""
=== PORTFOLIO CONNECTION SUMMARY ===
Source: {portfolio_data.get('source', 'Unknown')}
Last Updated: {portfolio_data.get('last_updated', 'Unknown')}

"""
        
        if portfolio_data.get('source') == 'indstocks_api':
            holdings = portfolio_data.get('holdings', {}).get('data', [])
            positions = portfolio_data.get('positions', {}).get('data', [])
            
            summary += f"Stock Holdings: {len(holdings)}\n"
            summary += f"Active Positions: {len(positions)}\n"
            
            total_value = 0
            for holding in holdings:
                total_value += holding.get('holding_value', 0)
            
            for position in positions:
                total_value += position.get('position_value', 0)
            
            summary += f"Total Portfolio Value: ₹{total_value:,.2f}\n"
            
        elif portfolio_data.get('source') in ['csv_import', 'manual_entry']:
            if 'portfolio' in portfolio_data:
                items = portfolio_data['portfolio']
                summary += f"Total Holdings: {len(items)}\n"
                summary += f"Total Investment: ₹{portfolio_data.get('total_investment', 0):,.2f}\n"
                
                if 'total_current_value' in portfolio_data:
                    summary += f"Current Value: ₹{portfolio_data['total_current_value']:,.2f}\n"
                    summary += f"Total Returns: ₹{portfolio_data['total_returns']:,.2f}\n"
                    return_pct = (portfolio_data['total_returns'] / portfolio_data['total_investment'] * 100) if portfolio_data['total_investment'] > 0 else 0
                    summary += f"Return Percentage: {return_pct:.2f}%\n"
        
        return summary


# Example usage and demo
def main():
    print("🔗 Portfolio Connection Demo\n")
    
    connector = PortfolioConnector()
    
    # Method 1: Connect via IndStocks API
    print("=== Method 1: IndStocks API Connection ===")
    indstocks_data = connector.connect_indstocks_portfolio()
    print(connector.generate_portfolio_summary(indstocks_data))
    
    # Method 2: Create CSV template
    print("\n=== Method 2: CSV Import ===")
    connector.create_sample_csv_template('portfolio_template.csv')
    
    # Method 3: Manual entry example
    print("\n=== Method 3: Manual Entry ===")
    manual_holdings = [
        {
            'symbol': 'RELIANCE',
            'quantity': 50,
            'avg_price': 2500.50,
            'category': 'stock'
        },
        {
            'scheme_code': '125497',
            'units': 100,
            'avg_nav': 180.25,
            'category': 'mutual_fund'
        }
    ]
    
    manual_data = connector.add_manual_holdings(manual_holdings)
    print(connector.generate_portfolio_summary(manual_data))
    
    print("\n✅ Portfolio connection methods demonstrated!")


if __name__ == "__main__":
    main()
