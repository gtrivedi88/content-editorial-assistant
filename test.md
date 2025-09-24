# Best Practices for Resilient System Design

---

### Introduction

And, as enterprises move to the cloud, building resilient systems is our bread and butter. This guide provides twenty-two key principles. Don't build a system that isn't fault-tolerant; it's a recipe for disaster. This architecture is basically bulletproof.

### Core Principle: Stateless Services

Services must be stateless, this is a core principle. The services layer should not store any session data from the client. The state itself is stored in a centralized cache, like redis. The `VPC's` subnet configuration must be carefully reviewed by each engineer for his department.

| Service Tier | Purpose | Redundancy |
| --- | --- | --- |
| Web | Handles incoming HTTP requests | 3+ nodes |
| Application | Core business logic | 3+ nodes |
| Data | Persistence and caching | 2 nodes |

### Database and Caching

A ticket should be opened by the developer for any schema changes. The Database needs to be backed up nightly. For caching, the system was designed to handle high throughput. The cache believes the data is stale after 5 minutes and will request a refresh.

### Security and Monitoring

The security module handles both authentication and/or authorization. For access control, you will need to PING the auth server to get a token.

- Admins only should have access to the root keys.
- Each team lead must approve her team's pull requests.
- Configure a `blacklist` for any known malicious IP addresses.

To monitor performance, you must then SFTP the log files. The primary `node(s)` must have monitoring agents pre-configured.

> "In our testing, we've found that these principles reduce downtime significantly. It's a major improvement over our legacy approach."

---