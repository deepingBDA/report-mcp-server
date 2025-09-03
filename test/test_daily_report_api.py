"""Test script for daily report API endpoint."""

import httpx
import asyncio
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
BASE_URL = "http://192.168.49.157:8002"  # Report server URL
DAILY_REPORT_ENDPOINT = f"{BASE_URL}/mcp/tools/daily-report-email"


async def test_daily_report_api():
    """Test the daily report API endpoint."""
    logger.info("=== Testing Daily Report API ===")
    
    try:
        # Calculate yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"Testing with date: {yesterday}")
        
        # Call the daily report API
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
            logger.info(f"Calling API: {DAILY_REPORT_ENDPOINT}")
            logger.info(f"Parameters: report_date={yesterday}")
            
            response = await client.post(
                DAILY_REPORT_ENDPOINT,
                params={"report_date": yesterday}
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Response result: {result.get('result')}")
                logger.info(f"Message: {result.get('message')}")
                
                if result.get("result") == "success":
                    logger.info("✅ Daily report API test PASSED!")
                    
                    # Log additional details
                    details = result.get("details", {})
                    if details:
                        logger.info(f"Summary length: {details.get('summary_length')} characters")
                        logger.info(f"HTML length: {details.get('html_length')} characters")
                        logger.info(f"Email recipients: {details.get('email_recipients')}")
                        logger.info(f"Execution time: {result.get('execution_time')}")
                    
                    return True
                    
                else:
                    logger.error(f"❌ Daily report API test FAILED: {result.get('message')}")
                    logger.error(f"Error details: {result.get('error_details')}")
                    return False
                    
            else:
                logger.error(f"❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error("❌ API call timed out after 5 minutes")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False


async def test_daily_report_status():
    """Test the daily report status endpoint."""
    logger.info("\n=== Testing Daily Report Status ===")
    
    try:
        status_endpoint = f"{BASE_URL}/mcp/tools/daily-report-status"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Calling: {status_endpoint}")
            
            response = await client.get(status_endpoint)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Status: {result.get('status')}")
                logger.info(f"Service: {result.get('service')}")
                
                config = result.get("configuration", {})
                if config:
                    logger.info(f"Configuration:")
                    for key, value in config.items():
                        logger.info(f"  {key}: {value}")
                
                logger.info("✅ Daily report status test PASSED!")
                return True
                
            else:
                logger.error(f"❌ Status check failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Status test failed: {e}")
        return False


async def test_daily_report_with_sample_data():
    """Test the daily report test endpoint with sample data."""
    logger.info("\n=== Testing Daily Report with Sample Data ===")
    
    try:
        test_endpoint = f"{BASE_URL}/mcp/tools/daily-report-test"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Calling: {test_endpoint}")
            
            response = await client.post(
                test_endpoint,
                params={"use_sample_data": True}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Result: {result.get('result')}")
                logger.info(f"Message: {result.get('message')}")
                logger.info(f"Test mode: {result.get('test_mode')}")
                
                workflow_steps = result.get("workflow_steps", {})
                if workflow_steps:
                    logger.info("Workflow steps:")
                    for step, status in workflow_steps.items():
                        logger.info(f"  {step}: {status}")
                
                logger.info("✅ Sample data test PASSED!")
                return True
                
            else:
                logger.error(f"❌ Sample data test failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Sample data test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("Starting Daily Report API Tests...")
    logger.info(f"Target server: {BASE_URL}")
    
    tests = [
        ("Daily Report Status", test_daily_report_status),
        ("Daily Report with Sample Data", test_daily_report_with_sample_data),
        ("Daily Report API (Real)", test_daily_report_api),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
    else:
        logger.error(f"❌ {total - passed} tests failed")


if __name__ == "__main__":
    asyncio.run(main())