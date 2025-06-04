import hazelcast
import threading
import time

def client_task(client_id):
    # Create a separate Hazelcast client for each thread
    client = hazelcast.HazelcastClient()
    
    try:
        print(f"Client {client_id} connected and starting increments with optimistic locks...")
        
        # Get the distributed map
        distributed_map = client.get_map("counter-map-optimistic").blocking()
        
        # Increment counter 10,000 times with optimistic locking
        for k in range(10_000):
            success = False
            retries = 0
            
            # Keep trying until the update succeeds
            while not success:
                # Read current value
                old_value = distributed_map.get("key")
                new_value = old_value + 1
                
                # Try to replace only if the value is still what we expect
                success = distributed_map.replace_if_same("key", old_value, new_value)
                retries += 1
                
                # Small sleep to prevent tight loops
                if not success:
                    time.sleep(0.001)
            
            if k % 1000 == 0:
                print(f"Client {client_id}: Completed {k} iterations")
        
        final_value = distributed_map.get("key")
        print(f"Client {client_id} finished - Current counter value: {final_value}")
        
    finally:
        client.shutdown()

def main():
    print("Starting concurrent optimistic locks test with 3 clients...")
    
    # Reset the counter in the map (create a temporary client)
    setup_client = hazelcast.HazelcastClient()
    try:
        setup_map = setup_client.get_map("counter-map-optimistic").blocking()
        setup_map.put("key", 0)
        print("Counter reset to 0")
    finally:
        setup_client.shutdown()
    
    # Create 3 threads, each with its own Hazelcast client
    threads = []
    start_time = time.time()
    
    for i in range(3):
        thread = threading.Thread(target=client_task, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check final value (create a temporary client)
    check_client = hazelcast.HazelcastClient()
    try:
        check_map = check_client.get_map("counter-map-optimistic").blocking()
        final_value = check_map.get("key")
        end_time = time.time()
        execution_time = end_time - start_time
        
        print("\n===== RESULTS =====")
        print(f"Final counter value: {final_value}")
        print(f"Expected value: 30,000")
        print(f"Total execution time: {execution_time:.4f} seconds")
    finally:
        check_client.shutdown()

if __name__ == "__main__":
    main()
