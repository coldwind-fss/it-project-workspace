import { api as remaining } from './index'
import { portfolioClient } from './portfolio'
import { workClient } from './work'
import { identityClient } from './identity'
// Preserve compatibility calls alongside the typed domain clients.
export const api = { ...remaining, ...portfolioClient, ...workClient, ...identityClient }
