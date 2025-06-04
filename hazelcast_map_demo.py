import hazelcast
import time

def main():
    client = hazelcast.HazelcastClient()
    
    try:
        distributed_map = client.get_map("demo-map").blocking()
        
        print("Starting to fill the distributed map with entries (keys 0-1000)...")
        
        for i in range(1001):
            distributed_map.put(i, f"Value-{i}")
            
            if i % 100 == 0:
                print(f"Added entries up to key {i}")
        
        map_size = distributed_map.size()
        print(f"Map created with {map_size} entries")

        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down client...")
    finally:
        client.shutdown()
        print("Client shut down")

if __name__ == "__main__":
    main()
