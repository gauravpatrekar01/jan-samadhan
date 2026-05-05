#!/usr/bin/env python3
"""
Test admin access to KPIs
"""
import requests

def test_admin_kpis():
    print("🔧 TESTING ADMIN ACCESS TO KPIS")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Try common admin credentials
    admin_logins = [
        {'email': 'admin@example.com', 'password': 'admin123'},
        {'email': 'admin@jansamadhan.com', 'password': 'admin123'},
        {'email': 'testadmin@example.com', 'password': 'TestAdmin123!@#'},
        {'email': 'administrator@example.com', 'password': 'Admin123!@#'},
    ]
    
    for login_data in admin_logins:
        try:
            login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
            print(f"Trying {login_data['email']}: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token = login_response.json()['data']['token']
                headers = {'Authorization': f'Bearer {token}'}
                
                # Test dashboard KPIs
                kpis_response = requests.get(f"{base_url}/api/kpis/dashboard", headers=headers)
                print(f"Dashboard KPIs: {kpis_response.status_code}")
                
                if kpis_response.status_code == 200:
                    data = kpis_response.json()
                    print("✅ Dashboard KPIs working with admin!")
                    
                    if data.get('success') and data.get('data'):
                        kpis = data['data']
                        print(f"   Performance score: {kpis.get('performance_score', 'N/A')}/100")
                        print(f"   Resolution rate: {kpis.get('resolution_rate', 'N/A')}%")
                        print(f"   Avg resolution time: {kpis.get('avg_resolution_time_hours', 'N/A')}h")
                        print(f"   SLA compliance: {kpis.get('sla_compliance_rate', 'N/A')}%")
                    
                    # Test department KPIs
                    dept_response = requests.get(f"{base_url}/api/kpis/department", headers=headers)
                    print(f"Department KPIs: {dept_response.status_code}")
                    
                    if dept_response.status_code == 200:
                        print("✅ Department KPIs also working!")
                    
                    break
                else:
                    print(f"Dashboard KPIs error: {kpis_response.text[:200]}")
            else:
                print(f"Login failed: {login_response.text[:100]}")
                
        except Exception as e:
            print(f"Error with {login_data['email']}: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 ADMIN KPIS TEST COMPLETE")

if __name__ == "__main__":
    test_admin_kpis()
