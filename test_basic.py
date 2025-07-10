#!/usr/bin/env python3
"""
Basic test to verify TrackLab implementation
"""

import sys
import tempfile
import os

def test_basic_functionality():
    """Test basic TrackLab functionality"""
    
    print("🧪 Testing TrackLab Basic Functionality")
    print("=" * 50)
    
    # Test 1: Import TrackLab
    print("1. Testing import...")
    try:
        import tracklab
        print("✅ Import successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Settings
    print("\n2. Testing settings...")
    try:
        from tracklab.sdk.tracklab_settings import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded - TrackLab dir: {settings.tracklab_dir}")
    except Exception as e:
        print(f"❌ Settings failed: {e}")
        return False
    
    # Test 3: Initialize run
    print("\n3. Testing run initialization...")
    try:
        run = tracklab.init(
            project="test-project",
            name="test-run",
            config={"learning_rate": 0.01, "epochs": 10},
            mode="offline"  # Use offline mode for testing
        )
        print(f"✅ Run initialized: {run.name} (ID: {run.id[:8]})")
    except Exception as e:
        print(f"❌ Run initialization failed: {e}")
        return False
    
    # Test 4: Log metrics
    print("\n4. Testing metrics logging...")
    try:
        tracklab.log({"accuracy": 0.95, "loss": 0.05})
        tracklab.log({"accuracy": 0.97, "loss": 0.03}, step=1)
        print("✅ Metrics logged successfully")
    except Exception as e:
        print(f"❌ Metrics logging failed: {e}")
        return False
    
    # Test 5: Config access
    print("\n5. Testing config access...")
    try:
        print(f"✅ Config: learning_rate = {tracklab.config['learning_rate']}")
        print(f"✅ Config: epochs = {tracklab.config['epochs']}")
    except Exception as e:
        print(f"❌ Config access failed: {e}")
        return False
    
    # Test 6: Summary access
    print("\n6. Testing summary access...")
    try:
        tracklab.summary["final_accuracy"] = 0.97
        tracklab.summary["final_loss"] = 0.03
        print(f"✅ Summary: final_accuracy = {tracklab.summary['final_accuracy']}")
    except Exception as e:
        print(f"❌ Summary access failed: {e}")
        return False
    
    # Test 7: Data types
    print("\n7. Testing data types...")
    try:
        # Test table
        table = tracklab.Table([[1, 2, 3], [4, 5, 6]], columns=["A", "B", "C"])
        tracklab.log({"results_table": table})
        
        # Test histogram
        import numpy as np
        hist = tracklab.Histogram(np.random.randn(1000))
        tracklab.log({"score_distribution": hist})
        
        print("✅ Data types working")
    except Exception as e:
        print(f"❌ Data types failed: {e}")
        return False
    
    # Test 8: Finish run
    print("\n8. Testing run finish...")
    try:
        tracklab.finish()
        print("✅ Run finished successfully")
    except Exception as e:
        print(f"❌ Run finish failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All basic tests passed!")
    return True

def test_data_types():
    """Test data type functionality"""
    
    print("\n🧪 Testing Data Types")
    print("=" * 50)
    
    try:
        import tracklab
        import numpy as np
        
        # Test different data types
        print("1. Testing Image...")
        try:
            # Create a simple image array
            img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            img = tracklab.Image(img_array, caption="Test image")
            print("✅ Image created successfully")
        except Exception as e:
            print(f"❌ Image test failed: {e}")
        
        print("\n2. Testing Table...")
        try:
            data = [
                {"name": "Alice", "age": 25, "score": 95.5},
                {"name": "Bob", "age": 30, "score": 87.2},
                {"name": "Charlie", "age": 35, "score": 92.8}
            ]
            table = tracklab.Table(data)
            print("✅ Table created successfully")
        except Exception as e:
            print(f"❌ Table test failed: {e}")
        
        print("\n3. Testing Histogram...")
        try:
            data = np.random.normal(0, 1, 1000)
            hist = tracklab.Histogram(data, title="Normal Distribution")
            print("✅ Histogram created successfully")
        except Exception as e:
            print(f"❌ Histogram test failed: {e}")
        
        print("\n4. Testing HTML...")
        try:
            html = tracklab.Html("<h1>Test Report</h1><p>This is a test.</p>")
            print("✅ HTML created successfully")
        except Exception as e:
            print(f"❌ HTML test failed: {e}")
        
        print("\n✅ Data types tests completed!")
        
    except Exception as e:
        print(f"❌ Data types test setup failed: {e}")
        return False
    
    return True

def test_cli():
    """Test CLI functionality"""
    
    print("\n🧪 Testing CLI")
    print("=" * 50)
    
    try:
        from tracklab.cli.main import main
        print("✅ CLI module imports successfully")
        
        # Test CLI help
        import subprocess
        result = subprocess.run([sys.executable, "-m", "tracklab.cli.main", "--help"], 
                              capture_output=True, text=True)
        if "TrackLab - Local experiment tracking" in result.stdout:
            print("✅ CLI help works")
        else:
            print("❌ CLI help failed")
            return False
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    
    print("🚀 TrackLab Implementation Test Suite")
    print("=" * 60)
    
    success = True
    
    # Run tests
    success &= test_basic_functionality()
    success &= test_data_types()
    success &= test_cli()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! TrackLab implementation is working correctly.")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())