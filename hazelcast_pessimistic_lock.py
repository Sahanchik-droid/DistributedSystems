import hazelcast
import threading
import time

def client_task(client_id):
    # Create a separate Hazelcast client for each thread
    client = hazelcast.HazelcastClient()
    
    try:
        print(f"Client {client_id} connected and starting increments with pessimistic locks...")
        
        # Get the distributed map
        distributed_map = client.get_map("counter-map-pessimistic").blocking()
        
        # Initialize counter to 0 if it doesn't exist (only first client will succeed)
        distributed_map.put_if_absent("key", 0)
        
        # Increment counter 10,000 times with pessimistic locking
        for k in range(10_000):
            # Acquire the lock before reading and updating
            distributed_map.lock("key")
            try:
                value = distributed_map.get("key")
                value += 1
                distributed_map.put("key", value)
            finally:
                # Always release the lock
                distributed_map.unlock("key")
                
            if k % 1000 == 0:
                print(f"Client {client_id}: Completed {k} iterations")
        
        final_value = distributed_map.get("key")
        print(f"Client {client_id} finished - Current counter value: {final_value}")
        
    finally:
        client.shutdown()

def main():
    print("Starting concurrent pessimistic locks test with 3 clients...")
    
    # Reset the counter in the map (create a temporary client)
    setup_client = hazelcast.HazelcastClient()
    try:
        setup_map = setup_client.get_map("counter-map-pessimistic").blocking()
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
        check_map = check_client.get_map("counter-map-pessimistic").blocking()
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
