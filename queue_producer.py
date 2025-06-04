import hazelcast
import time

def main():
    client = hazelcast.HazelcastClient()
    
    try:
        print("Producer starting - will add items 1-100 to bounded queue (capacity 10)")
        
        # Get the distributed queue
        queue = client.get_queue("bounded-demo-queue").blocking()
        
        # Try to add 100 items to the queue
        for i in range(1, 101):
            start_time = time.time()
            print(f"Attempting to add item {i} to queue...")
            
            # offer_timeout waits up to the specified seconds if the queue is full
            # passing 0 would make it non-blocking (return immediately if full)
            # passing a negative value means wait indefinitely
            success = queue.offer(i, 5)  
            
            elapsed = time.time() - start_time
            
            if success:
                print(f"Added item {i} to queue (took {elapsed:.2f} seconds)")
            else:
                print(f"Failed to add item {i} to queue after {elapsed:.2f} seconds - queue is full!")
                
                # Print the current queue size to verify it's full
                print(f"Current queue size: {queue.size()}")
                
                # If you want to keep trying until it succeeds:
                # queue.put(i)  # This will block indefinitely until space is available
            
            # Small delay between operations
            time.sleep(0.001)
        
        print("Producer finished attempting to add all items")
        
    finally:
        client.shutdown()

if __name__ == "__main__":
    main()
