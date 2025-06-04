import hazelcast
import time
import sys
import random

def main(consumer_id):
    client = hazelcast.HazelcastClient()
    
    try:
        print(f"Consumer {consumer_id} starting - will read from bounded queue")
        
        # Get the distributed queue
        queue = client.get_queue("bounded-demo-queue").blocking()
        
        item_count = 0
        
        # Continue trying to read from the queue
        while True:
            # Poll with a timeout - returns None if no item is available
            item = queue.poll(timeout=1)
            
            if item is not None:
                item_count += 1
                print(f"Consumer {consumer_id} received item: {item} (total received: {item_count})")
                
                # Simulate some processing time (randomized)
                processing_time = random.uniform(0.1, 0.5)
                time.sleep(processing_time)
            else:
                print(f"Consumer {consumer_id} - no items available...")
                
                # Check if queue is empty and producer might be done
                if queue.size() == 0 and item_count > 0:
                    print(f"Queue appears empty and we've received items before - checking if we're done")
                    time.sleep(2)  # Wait a bit longer to be sure
                    if queue.size() == 0:
                        break
        
        print(f"Consumer {consumer_id} finished, processed {item_count} items")
        
    finally:
        client.shutdown()

if __name__ == "__main__":
    # Take consumer ID from command line argument, default to 1
    consumer_id = 1
    if len(sys.argv) > 1:
        consumer_id = sys.argv[1]
    
    main(consumer_id)
