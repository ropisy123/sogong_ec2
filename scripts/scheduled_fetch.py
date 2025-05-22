import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.asset_manager import AssetManager
from adapters.asset_repository import AssetRepository

def main():
    manager = AssetManager(AssetRepository())
    manager.update_all_assets()

if __name__ == "__main__":
    main()
