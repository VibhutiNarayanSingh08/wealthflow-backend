"""
Mutual Funds Integration for IndStocks Investment App
Since IndStocks API doesn't support mutual funds, this provides integration with external APIs
"""

import requests
import os
from typing import Dict, List
from datetime import datetime

class MutualFundsManager:
    def __init__(self, api_key: str = None):
        # mfapi.in is FREE - no API key required!
        self.api_key = api_key or os.getenv('MF_API_KEY')  # Optional for other APIs
        self.base_urls = {
            'mfapi': 'https://api.mfapi.in',  # FREE API - no key needed
            'captnemo': 'https://mf.captnemo.in',  # FREE API - no key needed
            'rapidapi': 'https://india-mutual-funds-portfolio-holding.p.rapidapi.com'  # Requires key
        }
    
    def get_all_mf_schemes(self) -> Dict:
        """Get all available mutual fund schemes"""
        try:
            url = f"{self.base_urls['mfapi']}/mf"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching MF schemes: {e}")
            return {}
    
    def get_mf_scheme_info(self, scheme_code: str) -> Dict:
        """Get specific mutual fund scheme information"""
        try:
            url = f"{self.base_urls['mfapi']}/mf/{scheme_code}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching MF scheme {scheme_code}: {e}")
            return {}
    
    def get_latest_nav(self, scheme_code: str) -> Dict:
        """Get latest NAV for a mutual fund scheme"""
        try:
            url = f"{self.base_urls['mfapi']}/mf/{scheme_code}/latest"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching latest NAV for {scheme_code}: {e}")
            return {}
    
    def get_mf_nav_history(self, scheme_code: str, days: int = 365) -> Dict:
        """Get historical NAV data for a mutual fund scheme"""
        try:
            url = f"{self.base_urls['mfapi']}/mf/{scheme_code}/nav"
            params = {'days': days}
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NAV history for {scheme_code}: {e}")
            return {}
    
    def search_mutual_funds(self, query: str) -> List[Dict]:
        """Search mutual funds by name or AMC"""
        schemes = self.get_all_mf_schemes()
        if not schemes:
            return []
        
        results = []
        query_lower = query.lower()
        
        for scheme in schemes.get('data', []):
            if (query_lower in scheme.get('schemeName', '').lower() or 
                query_lower in scheme.get('amcName', '').lower()):
                results.append(scheme)
        
        return results[:20]  # Limit to 20 results
    
    def get_portfolio_analysis(self, folio_numbers: List[str]) -> Dict:
        """Analyze mutual fund portfolio across multiple folios"""
        portfolio_summary = {
            'total_investment': 0,
            'current_value': 0,
            'total_returns': 0,
            'return_percentage': 0,
            'schemes': [],
            'amc_distribution': {},
            'category_distribution': {}
        }
        
        for folio in folio_numbers:
            folio_data = self.get_folio_details(folio)
            if folio_data:
                self._process_folio_data(folio_data, portfolio_summary)
        
        # Calculate portfolio metrics
        if portfolio_summary['total_investment'] > 0:
            portfolio_summary['return_percentage'] = (
                portfolio_summary['total_returns'] / portfolio_summary['total_investment'] * 100
            )
        
        return portfolio_summary
    
    def get_folio_details(self, folio_number: str) -> Dict:
        """Get details for a specific folio (simulated)"""
        # Note: This is a placeholder implementation
        # In real scenarios, you'd need to integrate with CAMS/Karvy or your broker's MF API
        return {
            'folio_number': folio_number,
            'schemes': [
                {
                    'scheme_code': '120503',
                    'scheme_name': 'HDFC Mid-Cap Opportunities Fund',
                    'amc': 'HDFC',
                    'category': 'Mid Cap',
                    'units': 150.5,
                    'avg_cost': 85.50,
                    'current_nav': 112.30,
                    'investment_value': 12867.75,
                    'current_value': 16901.15,
                    'returns': 4033.40
                }
            ]
        }
    
    def _process_folio_data(self, folio_data: Dict, portfolio_summary: Dict):
        """Process folio data and update portfolio summary"""
        for scheme in folio_data.get('schemes', []):
            portfolio_summary['total_investment'] += scheme.get('investment_value', 0)
            portfolio_summary['current_value'] += scheme.get('current_value', 0)
            portfolio_summary['total_returns'] += scheme.get('returns', 0)
            
            # Update AMC distribution
            amc = scheme.get('amc', 'Unknown')
            portfolio_summary['amc_distribution'][amc] = (
                portfolio_summary['amc_distribution'].get(amc, 0) + scheme.get('current_value', 0)
            )
            
            # Update category distribution
            category = scheme.get('category', 'Unknown')
            portfolio_summary['category_distribution'][category] = (
                portfolio_summary['category_distribution'].get(category, 0) + scheme.get('current_value', 0)
            )
            
            portfolio_summary['schemes'].append(scheme)
    
    def generate_mf_report(self, folio_numbers: List[str]) -> str:
        """Generate comprehensive mutual fund portfolio report"""
        analysis = self.get_portfolio_analysis(folio_numbers)
        
        report = f"""
=== MUTUAL FUND PORTFOLIO REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PORTFOLIO SUMMARY:
- Total Investment: ₹{analysis['total_investment']:,.2f}
- Current Value: ₹{analysis['current_value']:,.2f}
- Total Returns: ₹{analysis['total_returns']:,.2f}
- Return Percentage: {analysis['return_percentage']:.2f}%

AMC DISTRIBUTION:
"""
        
        for amc, value in analysis['amc_distribution'].items():
            percentage = (value / analysis['current_value'] * 100) if analysis['current_value'] > 0 else 0
            report += f"- {amc}: ₹{value:,.2f} ({percentage:.1f}%)\n"
        
        report += "\nCATEGORY DISTRIBUTION:\n"
        for category, value in analysis['category_distribution'].items():
            percentage = (value / analysis['current_value'] * 100) if analysis['current_value'] > 0 else 0
            report += f"- {category}: ₹{value:,.2f} ({percentage:.1f}%)\n"
        
        report += "\nINDIVIDUAL SCHEMES:\n"
        for scheme in analysis['schemes']:
            return_pct = (scheme['returns'] / scheme['investment_value'] * 100) if scheme['investment_value'] > 0 else 0
            report += f"""
- {scheme['scheme_name']} ({scheme['amc']})
  Category: {scheme['category']}
  Units: {scheme['units']}
  Avg Cost: ₹{scheme['avg_cost']:.2f}
  Current NAV: ₹{scheme['current_nav']:.2f}
  Investment: ₹{scheme['investment_value']:,.2f}
  Current Value: ₹{scheme['current_value']:,.2f}
  Returns: ₹{scheme['returns']:,.2f} ({return_pct:.2f}%)
"""
        
        return report
    
    def compare_schemes(self, scheme_codes: List[str]) -> Dict:
        """Compare multiple mutual fund schemes"""
        comparison = {
            'schemes': [],
            'performance_metrics': {}
        }
        
        for code in scheme_codes:
            scheme_info = self.get_mf_scheme_info(code)
            nav_history = self.get_mf_nav_history(code, 365)
            
            if scheme_info and nav_history:
                scheme_data = {
                    'scheme_code': code,
                    'name': scheme_info.get('schemeName', 'Unknown'),
                    'amc': scheme_info.get('amcName', 'Unknown'),
                    'category': scheme_info.get('category', 'Unknown'),
                    'nav_history': nav_history.get('data', []),
                    'latest_nav': nav_history.get('data', [{}])[0].get('nav', 0) if nav_history.get('data') else 0
                }
                comparison['schemes'].append(scheme_data)
        
        return comparison


# Example usage
def main():
    # Initialize mutual funds manager
    mf_manager = MutualFundsManager()
    
    # Search for mutual funds
    print("=== SEARCHING MUTUAL FUNDS ===")
    results = mf_manager.search_mutual_funds("HDFC Mid Cap")
    for result in results[:5]:
        print(f"- {result.get('schemeName', 'N/A')} ({result.get('schemeCode', 'N/A')})")
    
    # Generate portfolio report
    print("\n=== MUTUAL FUND PORTFOLIO REPORT ===")
    folio_numbers = ['123456789', '987654321']  # Example folio numbers
    report = mf_manager.generate_mf_report(folio_numbers)
    print(report)
    
    # Compare schemes
    print("\n=== SCHEME COMPARISON ===")
    scheme_codes = ['120503', '118726']  # Example scheme codes
    comparison = mf_manager.compare_schemes(scheme_codes)
    
    for scheme in comparison['schemes']:
        print(f"- {scheme['name']}: Latest NAV ₹{scheme['latest_nav']:.2f}")


if __name__ == "__main__":
    main()
