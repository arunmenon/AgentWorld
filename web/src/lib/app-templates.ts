import type { AppCategory, ActionDefinition, StateField } from './api'

export interface AppTemplate {
  id: string
  name: string
  description: string
  category: AppCategory
  icon: string
  actions: ActionDefinition[]
  state_schema: StateField[]
  initial_config: Record<string, unknown>
}

export const appTemplates: AppTemplate[] = [
  {
    id: 'payment',
    name: 'Payment App',
    description: 'Transfer money between users with balance tracking',
    category: 'payment',
    icon: '💳',
    actions: [
      {
        name: 'check_balance',
        description: 'View your current balance',
        parameters: {},
        returns: { balance: 'number' },
        logic: [
          {
            type: 'return',
            value: { balance: 'agent.balance' },
          },
        ],
      },
      {
        name: 'transfer',
        description: 'Send money to another user',
        parameters: {
          to: { type: 'string', required: true, description: 'Recipient agent ID' },
          amount: { type: 'number', required: true, min_value: 0.01, max_value: 10000, description: 'Amount to transfer' },
          note: { type: 'string', required: false, max_length: 200, description: 'Optional note' },
        },
        returns: { transaction_id: 'string', new_balance: 'number' },
        logic: [
          { type: 'validate', condition: 'params.to != agent.id', error_message: 'Cannot transfer to yourself' },
          { type: 'validate', condition: 'params.amount <= agent.balance', error_message: 'Insufficient funds' },
          { type: 'update', target: 'agent.balance', operation: 'subtract', value: 'params.amount' },
          { type: 'update', target: 'agents[params.to].balance', operation: 'add', value: 'params.amount' },
          { type: 'notify', to: 'params.to', message: 'You received $${params.amount} from ${agent.name}', data: { type: 'received', amount: 'params.amount', from: 'agent.id' } },
          { type: 'return', value: { transaction_id: 'generate_id()', new_balance: 'agent.balance' } },
        ],
      },
      {
        name: 'request_money',
        description: 'Request money from another user',
        parameters: {
          from: { type: 'string', required: true, description: 'Agent ID to request from' },
          amount: { type: 'number', required: true, min_value: 0.01, description: 'Amount to request' },
          note: { type: 'string', required: false, description: 'Reason for request' },
        },
        returns: { request_id: 'string' },
        logic: [
          { type: 'validate', condition: 'params.from != agent.id', error_message: 'Cannot request from yourself' },
          { type: 'notify', to: 'params.from', message: '${agent.name} requested $${params.amount}', data: { type: 'request', amount: 'params.amount', from: 'agent.id' } },
          { type: 'return', value: { request_id: 'generate_id()' } },
        ],
      },
      {
        name: 'view_transactions',
        description: 'See recent transactions',
        parameters: {
          limit: { type: 'number', required: false, default: 10, description: 'Max transactions to return' },
        },
        returns: { transactions: 'array' },
        logic: [
          { type: 'return', value: { transactions: 'agent.transactions' } },
        ],
      },
    ],
    state_schema: [
      { name: 'balance', type: 'number', default: 1000, per_agent: true, description: 'Account balance', observable: true },
      { name: 'transactions', type: 'array', default: [], per_agent: true, description: 'Transaction history', observable: true },
      { name: 'fraud_score', type: 'number', default: 0, per_agent: true, description: 'Internal fraud risk score (0-100)', observable: false },
      { name: 'account_flags', type: 'array', default: [], per_agent: true, description: 'Internal account flags', observable: false },
    ],
    initial_config: {
      initial_balance: 1000,
      transaction_fee: 0,
      daily_limit: 10000,
    },
  },
  {
    id: 'shopping',
    name: 'Shopping App',
    description: 'Browse products, manage cart, and place orders',
    category: 'shopping',
    icon: '🛒',
    actions: [
      {
        name: 'browse_products',
        description: 'Browse available products',
        parameters: {
          category: { type: 'string', required: false, description: 'Filter by category' },
        },
        returns: { products: 'array' },
        logic: [
          { type: 'return', value: { products: 'state.products' } },
        ],
      },
      {
        name: 'add_to_cart',
        description: 'Add a product to your cart',
        parameters: {
          product_id: { type: 'string', required: true, description: 'Product to add' },
          quantity: { type: 'number', required: false, default: 1, description: 'Quantity' },
        },
        returns: { cart_total: 'number', items_count: 'number' },
        logic: [
          { type: 'update', target: 'agent.cart', operation: 'append', value: { product_id: 'params.product_id', quantity: 'params.quantity' } },
          { type: 'return', value: { cart_total: 'agent.cart_total', items_count: 'len(agent.cart)' } },
        ],
      },
      {
        name: 'view_cart',
        description: 'View items in your cart',
        parameters: {},
        returns: { items: 'array', total: 'number' },
        logic: [
          { type: 'return', value: { items: 'agent.cart', total: 'agent.cart_total' } },
        ],
      },
      {
        name: 'checkout',
        description: 'Place an order with items in cart',
        parameters: {
          shipping_address: { type: 'string', required: true, description: 'Delivery address' },
        },
        returns: { order_id: 'string', estimated_delivery: 'string' },
        logic: [
          { type: 'validate', condition: 'len(agent.cart) > 0', error_message: 'Cart is empty' },
          { type: 'update', target: 'agent.orders', operation: 'append', value: { id: 'generate_id()', items: 'agent.cart', address: 'params.shipping_address', status: 'pending' } },
          { type: 'update', target: 'agent.cart', operation: 'set', value: [] },
          { type: 'return', value: { order_id: 'generate_id()', estimated_delivery: '3-5 business days' } },
        ],
      },
      {
        name: 'track_order',
        description: 'Check order status',
        parameters: {
          order_id: { type: 'string', required: true, description: 'Order ID to track' },
        },
        returns: { status: 'string', location: 'string' },
        logic: [
          { type: 'return', value: { status: 'shipped', location: 'In transit' } },
        ],
      },
    ],
    state_schema: [
      { name: 'cart', type: 'array', default: [], per_agent: true, description: 'Shopping cart items', observable: true },
      { name: 'cart_total', type: 'number', default: 0, per_agent: true, description: 'Cart total price', observable: true },
      { name: 'orders', type: 'array', default: [], per_agent: true, description: 'Order history', observable: true },
      { name: 'products', type: 'array', default: [], per_agent: false, description: 'Available products', observable: true },
      { name: 'customer_tier', type: 'string', default: 'standard', per_agent: true, description: 'Internal customer tier', observable: false },
    ],
    initial_config: {
      currency: 'USD',
      tax_rate: 0.08,
    },
  },
  {
    id: 'email',
    name: 'Email App',
    description: 'Send, receive, and manage emails',
    category: 'communication',
    icon: '📧',
    actions: [
      {
        name: 'send_email',
        description: 'Send an email to another user',
        parameters: {
          to: { type: 'string', required: true, description: 'Recipient agent ID' },
          subject: { type: 'string', required: true, description: 'Email subject' },
          body: { type: 'string', required: true, description: 'Email content' },
        },
        returns: { message_id: 'string', sent_at: 'string' },
        logic: [
          { type: 'update', target: 'agent.sent', operation: 'append', value: { id: 'generate_id()', to: 'params.to', subject: 'params.subject', body: 'params.body', timestamp: 'timestamp()' } },
          { type: 'update', target: 'agents[params.to].inbox', operation: 'append', value: { id: 'generate_id()', from: 'agent.id', subject: 'params.subject', body: 'params.body', timestamp: 'timestamp()', read: false } },
          { type: 'notify', to: 'params.to', message: 'New email from ${agent.name}: ${params.subject}', data: { type: 'email', from: 'agent.id', subject: 'params.subject' } },
          { type: 'return', value: { message_id: 'generate_id()', sent_at: 'timestamp()' } },
        ],
      },
      {
        name: 'check_inbox',
        description: 'View received emails',
        parameters: {
          unread_only: { type: 'boolean', required: false, default: false, description: 'Only show unread' },
        },
        returns: { emails: 'array', unread_count: 'number' },
        logic: [
          { type: 'return', value: { emails: 'agent.inbox', unread_count: 'agent.unread_count' } },
        ],
      },
      {
        name: 'read_email',
        description: 'Read a specific email',
        parameters: {
          message_id: { type: 'string', required: true, description: 'Email ID to read' },
        },
        returns: { email: 'object' },
        logic: [
          { type: 'return', value: { email: 'agent.inbox[0]' } },
        ],
      },
      {
        name: 'reply',
        description: 'Reply to an email',
        parameters: {
          message_id: { type: 'string', required: true, description: 'Original email ID' },
          body: { type: 'string', required: true, description: 'Reply content' },
        },
        returns: { message_id: 'string' },
        logic: [
          { type: 'return', value: { message_id: 'generate_id()' } },
        ],
      },
    ],
    state_schema: [
      { name: 'inbox', type: 'array', default: [], per_agent: true, description: 'Received emails' },
      { name: 'sent', type: 'array', default: [], per_agent: true, description: 'Sent emails' },
      { name: 'unread_count', type: 'number', default: 0, per_agent: true, description: 'Unread email count' },
    ],
    initial_config: {},
  },
  {
    id: 'calendar',
    name: 'Calendar App',
    description: 'Manage events, reminders, and schedules',
    category: 'calendar',
    icon: '📅',
    actions: [
      {
        name: 'create_event',
        description: 'Create a new calendar event',
        parameters: {
          title: { type: 'string', required: true, description: 'Event title' },
          start_time: { type: 'string', required: true, description: 'Start time (ISO format)' },
          end_time: { type: 'string', required: true, description: 'End time (ISO format)' },
          attendees: { type: 'array', required: false, description: 'Agent IDs to invite' },
        },
        returns: { event_id: 'string' },
        logic: [
          { type: 'update', target: 'agent.events', operation: 'append', value: { id: 'generate_id()', title: 'params.title', start: 'params.start_time', end: 'params.end_time' } },
          { type: 'return', value: { event_id: 'generate_id()' } },
        ],
      },
      {
        name: 'view_schedule',
        description: 'View upcoming events',
        parameters: {
          date: { type: 'string', required: false, description: 'Specific date to view' },
        },
        returns: { events: 'array' },
        logic: [
          { type: 'return', value: { events: 'agent.events' } },
        ],
      },
      {
        name: 'set_reminder',
        description: 'Set a reminder',
        parameters: {
          message: { type: 'string', required: true, description: 'Reminder text' },
          remind_at: { type: 'string', required: true, description: 'When to remind' },
        },
        returns: { reminder_id: 'string' },
        logic: [
          { type: 'update', target: 'agent.reminders', operation: 'append', value: { id: 'generate_id()', message: 'params.message', time: 'params.remind_at' } },
          { type: 'return', value: { reminder_id: 'generate_id()' } },
        ],
      },
      {
        name: 'cancel_event',
        description: 'Cancel an event',
        parameters: {
          event_id: { type: 'string', required: true, description: 'Event to cancel' },
        },
        returns: { success: 'boolean' },
        logic: [
          { type: 'return', value: { success: true } },
        ],
      },
    ],
    state_schema: [
      { name: 'events', type: 'array', default: [], per_agent: true, description: 'Calendar events' },
      { name: 'reminders', type: 'array', default: [], per_agent: true, description: 'Reminders' },
    ],
    initial_config: {
      timezone: 'UTC',
    },
  },
  {
    id: 'messaging',
    name: 'Messaging App',
    description: 'Send and receive instant messages',
    category: 'social',
    icon: '💬',
    actions: [
      {
        name: 'send_message',
        description: 'Send a message to another user',
        parameters: {
          to: { type: 'string', required: true, description: 'Recipient agent ID' },
          text: { type: 'string', required: true, description: 'Message content' },
        },
        returns: { message_id: 'string', timestamp: 'string' },
        logic: [
          { type: 'update', target: 'agent.conversations[params.to]', operation: 'append', value: { id: 'generate_id()', from: 'agent.id', text: 'params.text', timestamp: 'timestamp()' } },
          { type: 'update', target: 'agents[params.to].conversations[agent.id]', operation: 'append', value: { id: 'generate_id()', from: 'agent.id', text: 'params.text', timestamp: 'timestamp()' } },
          { type: 'notify', to: 'params.to', message: 'New message from ${agent.name}: ${params.text}', data: { type: 'message', from: 'agent.id' } },
          { type: 'return', value: { message_id: 'generate_id()', timestamp: 'timestamp()' } },
        ],
      },
      {
        name: 'get_conversations',
        description: 'List all conversations',
        parameters: {},
        returns: { conversations: 'array' },
        logic: [
          { type: 'return', value: { conversations: 'agent.conversations' } },
        ],
      },
      {
        name: 'get_messages',
        description: 'Get messages in a conversation',
        parameters: {
          with: { type: 'string', required: true, description: 'Other agent ID' },
          limit: { type: 'number', required: false, default: 50, description: 'Max messages' },
        },
        returns: { messages: 'array' },
        logic: [
          { type: 'return', value: { messages: 'agent.conversations[params.with]' } },
        ],
      },
    ],
    state_schema: [
      { name: 'conversations', type: 'object', default: {}, per_agent: true, description: 'Message threads' },
    ],
    initial_config: {},
  },
  {
    id: 'blank',
    name: 'Blank App',
    description: 'Start from scratch with no predefined actions',
    category: 'custom',
    icon: '📝',
    actions: [],
    state_schema: [],
    initial_config: {},
  },
]
