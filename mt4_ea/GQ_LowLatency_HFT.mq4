//+------------------------------------------------------------------+
//|                                          GQ_LowLatency_HFT.mq4     |
//|                                    Gann-Ehlers Trading System     |
//|                                    Ultra Low Latency HFT EA       |
//+------------------------------------------------------------------+
#property copyright "Gann-Ehlers Trading System"
#property link      "https://github.com/gann-ehlers"
#property version   "1.00"
#property strict
#property description "Ultra Low Latency TCP Socket EA for HFT"

//--- Winsock imports
#import "ws2_32.dll"
   int WSAStartup(int wVersionRequired, int& lpWSAData[]);
   int WSACleanup();
   int socket(int af, int type, int protocol);
   int bind(int s, int& name[], int namelen);
   int listen(int s, int backlog);
   int accept(int s, int& addr[], int& addrlen);
   int connect(int s, int& name[], int namelen);
   int send(int s, string buf, int len, int flags);
   int recv(int s, int& buf[], int len, int flags);
   int closesocket(int s);
   int ioctlsocket(int s, long cmd, int& argp);
   int setsockopt(int s, int level, int optname, int& optval, int optlen);
   int getsockopt(int s, int level, int optname, int& optval, int& optlen);
   int WSAGetLastError();
#import

//--- Constants
#define AF_INET        2
#define SOCK_STREAM    1
#define IPPROTO_TCP    6
#define SOMAXCONN      5
#define SOCKET_ERROR   -1
#define INVALID_SOCKET -1

// TCP options
#define IPPROTO_TCP_LEVEL  6
#define TCP_NODELAY        1

// Socket level
#define SOL_SOCKET         0xFFFF
#define SO_REUSEADDR       4
#define SO_RCVBUF          0x1002
#define SO_SNDBUF          0x1001

// Non-blocking
#define FIONBIO            0x8004667E

//--- Input parameters
input string   Network_Settings = "=== Network Settings ===";
input int      TCP_PORT = 5557;
input int      MAX_CONNECTIONS = 8;
input int      SOCKET_TIMEOUT_MS = 100;
input int      RECV_BUFFER_SIZE = 262144;  // 256KB
input int      SEND_BUFFER_SIZE = 262144;  // 256KB

input string   Trading_Settings = "=== Trading Settings ===";
input int      MAGIC_NUMBER = 123456;
input string   ORDER_COMMENT = "HFT";
input int      MAX_SLIPPAGE = 0;  // Zero slippage for HFT

input string   Performance_Settings = "=== Performance Settings ===";
input bool     USE_SHARED_MEMORY = true;
input string   SHARED_MEMORY_NAME = "mt4_ticks.shm";
input int      SHARED_MEMORY_SIZE = 1048576;  // 1MB
input bool     SPIN_WAIT = true;
input int      TICK_THROTTLE_US = 100;  // Min microseconds between tick broadcasts

//--- Command types (must match Python)
enum CommandType {
   CMD_PING = 0,
   CMD_PONG = 1,
   CMD_HEARTBEAT = 2,
   CMD_STATUS = 3,
   CMD_ACCOUNT_INFO = 10,
   CMD_BALANCE = 11,
   CMD_EQUITY = 12,
   CMD_MARGIN = 13,
   CMD_SYMBOL_INFO = 20,
   CMD_TICK = 21,
   CMD_BARS = 22,
   CMD_QUOTE = 23,
   CMD_ORDER_SEND = 30,
   CMD_ORDER_MODIFY = 31,
   CMD_ORDER_CANCEL = 32,
   CMD_ORDER_CLOSE = 33,
   CMD_ORDER_STATUS = 34,
   CMD_POSITIONS = 40,
   CMD_POSITION_INFO = 41,
   CMD_POSITION_CLOSE = 42,
   CMD_SUBSCRIBE_TICK = 60,
   CMD_SUBSCRIBE_BAR = 61,
   CMD_UNSUBSCRIBE = 62
};

//--- Response status
enum ResponseStatus {
   STATUS_OK = 0,
   STATUS_ERROR = 1,
   STATUS_TIMEOUT = 2,
   STATUS_REJECTED = 3,
   STATUS_INVALID = 4,
   STATUS_NOT_CONNECTED = 5
};

//--- Global variables
int serverSocket = INVALID_SOCKET;
int clientSockets[];
bool isRunning = false;
string subscribedSymbols[];
datetime lastTickTime;
int lastTickUS = 0;

// Performance tracking
ulong totalCommands = 0;
ulong successfulCommands = 0;
ulong failedCommands = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Initialize Winsock
   int wsaData[64];
   if(WSAStartup(0x0202, wsaData) != 0)
   {
      Print("WSAStartup failed: ", WSAGetLastError());
      return INIT_FAILED;
   }
   
   // Create server socket
   serverSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
   if(serverSocket == INVALID_SOCKET)
   {
      Print("Socket creation failed: ", WSAGetLastError());
      WSACleanup();
      return INIT_FAILED;
   }
   
   // Set socket options
   int optVal = 1;
   if(setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR, optVal, 4) == SOCKET_ERROR)
   {
      Print("Setsockopt SO_REUSEADDR failed: ", WSAGetLastError());
   }
   
   optVal = RECV_BUFFER_SIZE;
   if(setsockopt(serverSocket, SOL_SOCKET, SO_RCVBUF, optVal, 4) == SOCKET_ERROR)
   {
      Print("Setsockopt SO_RCVBUF failed: ", WSAGetLastError());
   }
   
   optVal = SEND_BUFFER_SIZE;
   if(setsockopt(serverSocket, SOL_SOCKET, SO_SNDBUF, optVal, 4) == SOCKET_ERROR)
   {
      Print("Setsockopt SO_SNDBUF failed: ", WSAGetLastError());
   }
   
   optVal = 1;
   if(setsockopt(serverSocket, IPPROTO_TCP_LEVEL, TCP_NODELAY, optVal, 4) == SOCKET_ERROR)
   {
      Print("Setsockopt TCP_NODELAY failed: ", WSAGetLastError());
   }
   
   // Bind socket
   int sockAddr[4];
   sockAddr[0] = AF_INET;           // sin_family
   sockAddr[1] = (TCP_PORT << 16) & 0xFFFF0000;  // sin_port (big-endian)
   sockAddr[2] = 0;                  // sin_addr (0.0.0.0 = INADDR_ANY)
   sockAddr[3] = 0;                  // sin_zero padding
   
   if(bind(serverSocket, sockAddr, 16) == SOCKET_ERROR)
   {
      Print("Bind failed: ", WSAGetLastError());
      closesocket(serverSocket);
      WSACleanup();
      return INIT_FAILED;
   }
   
   // Listen
   if(listen(serverSocket, SOMAXCONN) == SOCKET_ERROR)
   {
      Print("Listen failed: ", WSAGetLastError());
      closesocket(serverSocket);
      WSACleanup();
      return INIT_FAILED;
   }
   
   // Set non-blocking mode
   int nonBlock = 1;
   if(ioctlsocket(serverSocket, FIONBIO, nonBlock) == SOCKET_ERROR)
   {
      Print("ioctlsocket failed: ", WSAGetLastError());
   }
   
   // Initialize client sockets array
   ArrayResize(clientSockets, MAX_CONNECTIONS);
   ArrayInitialize(clientSockets, INVALID_SOCKET);
   
   // Initialize subscribed symbols
   ArrayResize(subscribedSymbols, 0);
   
   isRunning = true;
   lastTickTime = TimeCurrent();
   
   Print("===============================================");
   Print("GQ Low Latency HFT EA v1.00 Started");
   Print("TCP Server listening on port: ", TCP_PORT);
   Print("Account: ", AccountNumber(), " Balance: ", AccountBalance());
   Print("Socket buffer sizes: RCV=", RECV_BUFFER_SIZE, " SND=", SEND_BUFFER_SIZE);
   Print("===============================================");
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   isRunning = false;
   
   // Close all client sockets
   for(int i = 0; i < ArraySize(clientSockets); i++)
   {
      if(clientSockets[i] != INVALID_SOCKET)
      {
         closesocket(clientSockets[i]);
         clientSockets[i] = INVALID_SOCKET;
      }
   }
   
   // Close server socket
   if(serverSocket != INVALID_SOCKET)
   {
      closesocket(serverSocket);
      serverSocket = INVALID_SOCKET;
   }
   
   // Cleanup Winsock
   WSACleanup();
   
   Print("===============================================");
   Print("GQ Low Latency HFT EA Stopped");
   Print("Total commands: ", totalCommands);
   Print("Successful: ", successfulCommands, " Failed: ", failedCommands);
   if(totalCommands > 0)
   {
      Print("Success rate: ", DoubleToString((double)successfulCommands / totalCommands * 100, 2), "%");
   }
   Print("===============================================");
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!isRunning) return;
   
   // Accept new connections
   AcceptConnections();
   
   // Process commands from all clients
   ProcessClientCommands();
   
   // Broadcast tick data if subscribed
   if(ArraySize(subscribedSymbols) > 0)
   {
      BroadcastTickData();
   }
}

//+------------------------------------------------------------------+
//| Accept new connections                                             |
//+------------------------------------------------------------------+
void AcceptConnections()
{
   int clientAddr[4];
   int addrLen = 16;
   
   int clientSock = accept(serverSocket, clientAddr, addrLen);
   
   if(clientSock != INVALID_SOCKET)
   {
      // Find free slot
      int slot = -1;
      for(int i = 0; i < ArraySize(clientSockets); i++)
      {
         if(clientSockets[i] == INVALID_SOCKET)
         {
            slot = i;
            break;
         }
      }
      
      if(slot >= 0)
      {
         // Set TCP_NODELAY
         int optVal = 1;
         setsockopt(clientSock, IPPROTO_TCP_LEVEL, TCP_NODELAY, optVal, 4);
         
         // Set non-blocking
         int nonBlock = 1;
         ioctlsocket(clientSock, FIONBIO, nonBlock);
         
         clientSockets[slot] = clientSock;
         Print("Client connected: slot=", slot, " socket=", clientSock);
      }
      else
      {
         // No free slot, reject connection
         closesocket(clientSock);
         Print("Connection rejected: no free slots");
      }
   }
}

//+------------------------------------------------------------------+
//| Process commands from all clients                                  |
//+------------------------------------------------------------------+
void ProcessClientCommands()
{
   for(int i = 0; i < ArraySize(clientSockets); i++)
   {
      int sock = clientSockets[i];
      if(sock == INVALID_SOCKET) continue;
      
      // Try to receive data (non-blocking)
      int recvBuffer[1024];  // 4KB buffer
      int bytesRead = recv(sock, recvBuffer, sizeof(recvBuffer), 0);
      
      if(bytesRead > 0)
      {
         // Process the received command
         totalCommands++;
         
         uchar data[];
         ArrayResize(data, bytesRead);
         for(int j = 0; j < bytesRead; j++)
         {
            data[j] = (uchar)(recvBuffer[j / 4] >> ((j % 4) * 8)) & 0xFF;
         }
         
         ProcessBinaryCommand(sock, data);
      }
      else if(bytesRead == 0)
      {
         // Connection closed
         Print("Client disconnected: slot=", i);
         closesocket(sock);
         clientSockets[i] = INVALID_SOCKET;
      }
      else
      {
         // Would block or error
         int error = WSAGetLastError();
         if(error != 10035)  // WSAEWOULDBLOCK
         {
            Print("Recv error: ", error, " slot=", i);
            closesocket(sock);
            clientSockets[i] = INVALID_SOCKET;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Process binary command                                             |
//+------------------------------------------------------------------+
void ProcessBinaryCommand(int sock, uchar& data[])
{
   if(ArraySize(data) < 11)
   {
      SendErrorResponse(sock, 0, STATUS_INVALID);
      failedCommands++;
      return;
   }
   
   // Parse header: cmdType(1) + requestId(8) + payloadLen(2)
   int cmdType = data[0];
   ulong requestId = 0;
   for(int i = 0; i < 8; i++)
   {
      requestId |= ((ulong)data[1 + i]) << (i * 8);
   }
   int payloadLen = data[9] | (data[10] << 8);
   
   // Get payload
   uchar payload[];
   if(payloadLen > 0 && ArraySize(data) >= 11 + payloadLen)
   {
      ArrayCopy(payload, data, 0, 11, payloadLen);
   }
   
   // Process command
   switch(cmdType)
   {
      case CMD_PING:
         SendPongResponse(sock, requestId);
         successfulCommands++;
         break;
         
      case CMD_ACCOUNT_INFO:
         SendAccountInfoResponse(sock, requestId);
         successfulCommands++;
         break;
         
      case CMD_BALANCE:
         SendBalanceResponse(sock, requestId);
         successfulCommands++;
         break;
         
      case CMD_EQUITY:
         SendEquityResponse(sock, requestId);
         successfulCommands++;
         break;
         
      case CMD_TICK:
         SendTickResponse(sock, requestId, payload);
         successfulCommands++;
         break;
         
      case CMD_POSITIONS:
         SendPositionsResponse(sock, requestId);
         successfulCommands++;
         break;
         
      case CMD_ORDER_SEND:
         ExecuteOrder(sock, requestId, payload);
         break;
         
      case CMD_ORDER_CLOSE:
         CloseOrderByTicket(sock, requestId, payload);
         break;
         
      case CMD_ORDER_MODIFY:
         ModifyOrder(sock, requestId, payload);
         break;
         
      case CMD_SUBSCRIBE_TICK:
         SubscribeSymbol(payload);
         SendSuccessResponse(sock, requestId);
         successfulCommands++;
         break;
         
      default:
         SendErrorResponse(sock, requestId, STATUS_INVALID);
         failedCommands++;
         break;
   }
}

//+------------------------------------------------------------------+
//| Send response                                                      |
//+------------------------------------------------------------------+
void SendResponse(int sock, ulong requestId, int status, uchar& payload[])
{
   // Build response header: status(1) + requestId(8) + payloadLen(2)
   uchar response[];
   int totalLen = 11 + ArraySize(payload);
   ArrayResize(response, totalLen);
   
   response[0] = (uchar)status;
   
   for(int i = 0; i < 8; i++)
   {
      response[1 + i] = (uchar)((requestId >> (i * 8)) & 0xFF);
   }
   
   response[9] = (uchar)(ArraySize(payload) & 0xFF);
   response[10] = (uchar)((ArraySize(payload) >> 8) & 0xFF);
   
   // Copy payload
   for(int i = 0; i < ArraySize(payload); i++)
   {
      response[11 + i] = payload[i];
   }
   
   // Send as string (workaround for MQL4)
   string sendStr = "";
   for(int i = 0; i < totalLen; i++)
   {
      sendStr += CharToString(response[i]);
   }
   
   send(sock, sendStr, totalLen, 0);
}

//+------------------------------------------------------------------+
//| Send PONG response                                                 |
//+------------------------------------------------------------------+
void SendPongResponse(int sock, ulong requestId)
{
   uchar payload[1];
   payload[0] = 1;  // PONG
   SendResponse(sock, requestId, STATUS_OK, payload);
}

//+------------------------------------------------------------------+
//| Send success response                                              |
//+------------------------------------------------------------------+
void SendSuccessResponse(int sock, ulong requestId)
{
   uchar payload[];
   ArrayResize(payload, 0);
   SendResponse(sock, requestId, STATUS_OK, payload);
}

//+------------------------------------------------------------------+
//| Send error response                                                |
//+------------------------------------------------------------------+
void SendErrorResponse(int sock, ulong requestId, int errorCode)
{
   uchar payload[];
   ArrayResize(payload, 0);
   SendResponse(sock, requestId, errorCode, payload);
}

//+------------------------------------------------------------------+
//| Send account info response                                         |
//+------------------------------------------------------------------+
void SendAccountInfoResponse(int sock, ulong requestId)
{
   // Build JSON-like response
   string json = "{";
   json += "\"login\":" + IntegerToString(AccountNumber()) + ",";
   json += "\"balance\":" + DoubleToString(AccountBalance(), 2) + ",";
   json += "\"equity\":" + DoubleToString(AccountEquity(), 2) + ",";
   json += "\"margin\":" + DoubleToString(AccountMargin(), 2) + ",";
   json += "\"free_margin\":" + DoubleToString(AccountFreeMargin(), 2) + ",";
   json += "\"margin_level\":" + DoubleToString(AccountMarginLevel(), 2) + ",";
   json += "\"leverage\":" + IntegerToString(AccountLeverage()) + ",";
   json += "\"currency\":\"" + AccountCurrency() + "\",";
   json += "\"profit\":" + DoubleToString(AccountProfit(), 2);
   json += "}";
   
   uchar payload[];
   StringToByteArray(json, payload);
   SendResponse(sock, requestId, STATUS_OK, payload);
}

//+------------------------------------------------------------------+
//| Send balance response                                              |
//+------------------------------------------------------------------+
void SendBalanceResponse(int sock, ulong requestId)
{
   // Binary: 8 bytes double
   uchar payload[8];
   double balance = AccountBalance();
   DoubleToByteArray(balance, payload);
   SendResponse(sock, requestId, STATUS_OK, payload);
}

//+------------------------------------------------------------------+
//| Send equity response                                               |
//+------------------------------------------------------------------+
void SendEquityResponse(int sock, ulong requestId)
{
   uchar payload[8];
   double equity = AccountEquity();
   DoubleToByteArray(equity, payload);
   SendResponse(sock, requestId, STATUS_OK, payload);
}

//+------------------------------------------------------------------+
//| Send tick response                                                 |
//+------------------------------------------------------------------+
void SendTickResponse(int sock, ulong requestId, uchar& payload[])
{
   if(ArraySize(payload) < 12)
   {
      SendErrorResponse(sock, requestId, STATUS_INVALID);
      return;
   }
   
   // Extract symbol from payload
   string symbol = ByteArrayToString(payload, 0, 12);
   symbol = StringTrimRight(symbol);
   
   if(!SymbolSelect(symbol, true))
   {
      SendErrorResponse(sock, requestId, STATUS_INVALID);
      return;
   }
   
   MqlTick tick;
   if(!SymbolInfoTick(symbol, tick))
   {
      SendErrorResponse(sock, requestId, STATUS_ERROR);
      return;
   }
   
   // Binary tick: symbol(12) + bid(8) + ask(8) + spread(8) + volume(8) + time(8) = 52 bytes
   uchar tickPayload[52];
   
   // Symbol
   StringToByteArrayFixed(symbol, tickPayload, 0, 12);
   
   int digits = (int)MarketInfo(symbol, MODE_DIGITS);
   double point = MarketInfo(symbol, MODE_POINT);
   
   // Bid
   DoubleToByteArray(tick.bid, tickPayload, 12);
   
   // Ask
   DoubleToByteArray(tick.ask, tickPayload, 20);
   
   // Spread
   DoubleToByteArray((tick.ask - tick.bid) / point, tickPayload, 28);
   
   // Volume
   LongToByteArray(tick.volume, tickPayload, 36);
   
   // Time (nanoseconds - using microseconds precision)
   LongToByteArray(tick.time_msc * 1000, tickPayload, 44);
   
   SendResponse(sock, requestId, STATUS_OK, tickPayload);
}

//+------------------------------------------------------------------+
//| Send positions response                                            |
//+------------------------------------------------------------------+
void SendPositionsResponse(int sock, ulong requestId)
{
   int total = OrdersTotal();
   
   // Each position: 60 bytes
   // ticket(8) + symbol(12) + side(1) + type(1) + volume(8) + openPrice(8) + sl(8) + tp(8) + profit(8) + magic(4) + time(8)
   
   uchar payload[];
   ArrayResize(payload, total * 60);
   int offset = 0;
   
   for(int i = 0; i < total; i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         // Ticket
         LongToByteArray(OrderTicket(), payload, offset);
         offset += 8;
         
         // Symbol
         StringToByteArrayFixed(OrderSymbol(), payload, offset, 12);
         offset += 12;
         
         // Side (0=BUY, 1=SELL)
         payload[offset] = (uchar)(OrderType() == OP_BUY ? 0 : 1);
         offset += 1;
         
         // Order type (0=MARKET, 1=LIMIT, 2=STOP)
         int orderType = 0;
         if(OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT) orderType = 1;
         if(OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP) orderType = 2;
         payload[offset] = (uchar)orderType;
         offset += 1;
         
         // Volume
         DoubleToByteArray(OrderLots(), payload, offset);
         offset += 8;
         
         // Open price
         DoubleToByteArray(OrderOpenPrice(), payload, offset);
         offset += 8;
         
         // SL
         DoubleToByteArray(OrderStopLoss(), payload, offset);
         offset += 8;
         
         // TP
         DoubleToByteArray(OrderTakeProfit(), payload, offset);
         offset += 8;
         
         // Profit
         DoubleToByteArray(OrderProfit(), payload, offset);
         offset += 8;
         
         // Magic
         IntToByteArray(OrderMagicNumber(), payload, offset);
         offset += 4;
         
         // Open time
         LongToByteArray(OrderOpenTime(), payload, offset);
         offset += 8;
      }
   }
   
   SendResponse(sock, requestId, STATUS_OK, payload);
}

//+------------------------------------------------------------------+
//| Execute order                                                      |
//+------------------------------------------------------------------+
void ExecuteOrder(int sock, ulong requestId, uchar& payload[])
{
   // Payload: symbol(12) + side(1) + type(1) + volume(8) + price(8) + sl(8) + tp(8) + slippage(4) + magic(4) + comment(32)
   
   if(ArraySize(payload) < 78)
   {
      SendErrorResponse(sock, requestId, STATUS_INVALID);
      failedCommands++;
      return;
   }
   
   string symbol = ByteArrayToString(payload, 0, 12);
   symbol = StringTrimRight(symbol);
   
   int side = payload[12];  // 0=BUY, 1=SELL
   int orderType = payload[13];  // 0=MARKET, 1=LIMIT, 2=STOP
   
   double volume = ByteArrayToDouble(payload, 14);
   double price = ByteArrayToDouble(payload, 22);
   double sl = ByteArrayToDouble(payload, 30);
   double tp = ByteArrayToDouble(payload, 38);
   int slippage = ByteArrayToInt(payload, 46);
   int magic = ByteArrayToInt(payload, 50);
   string comment = ByteArrayToString(payload, 54, 32);
   comment = StringTrimRight(comment);
   
   if(slippage == 0) slippage = MAX_SLIPPAGE;
   if(magic == 0) magic = MAGIC_NUMBER;
   if(StringLen(comment) == 0) comment = ORDER_COMMENT;
   
   int cmd;
   double execPrice;
   
   int digits = (int)MarketInfo(symbol, MODE_DIGITS);
   
   if(orderType == 0)  // MARKET
   {
      if(side == 0)  // BUY
      {
         cmd = OP_BUY;
         execPrice = MarketInfo(symbol, MODE_ASK);
      }
      else  // SELL
      {
         cmd = OP_SELL;
         execPrice = MarketInfo(symbol, MODE_BID);
      }
   }
   else if(orderType == 1)  // LIMIT
   {
      if(side == 0)
      {
         cmd = OP_BUYLIMIT;
         execPrice = price;
      }
      else
      {
         cmd = OP_SELLLIMIT;
         execPrice = price;
      }
   }
   else  // STOP
   {
      if(side == 0)
      {
         cmd = OP_BUYSTOP;
         execPrice = price;
      }
      else
      {
         cmd = OP_SELLSTOP;
         execPrice = price;
      }
   }
   
   execPrice = NormalizeDouble(execPrice, digits);
   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);
   
   int ticket = OrderSend(symbol, cmd, volume, execPrice, slippage, sl, tp, comment, magic, 0, clrNONE);
   
   if(ticket > 0)
   {
      successfulCommands++;
      
      // Return ticket in payload
      uchar responsePayload[8];
      LongToByteArray(ticket, responsePayload, 0);
      SendResponse(sock, requestId, STATUS_OK, responsePayload);
   }
   else
   {
      failedCommands++;
      SendErrorResponse(sock, requestId, STATUS_REJECTED);
   }
}

//+------------------------------------------------------------------+
//| Close order by ticket                                              |
//+------------------------------------------------------------------+
void CloseOrderByTicket(int sock, ulong requestId, uchar& payload[])
{
   if(ArraySize(payload) < 16)
   {
      SendErrorResponse(sock, requestId, STATUS_INVALID);
      failedCommands++;
      return;
   }
   
   ulong ticket = ByteArrayToLong(payload, 0);
   double volume = ByteArrayToDouble(payload, 8);
   
   if(OrderSelect((int)ticket, SELECT_BY_TICKET))
   {
      double closePrice;
      
      if(OrderType() == OP_BUY)
      {
         closePrice = MarketInfo(OrderSymbol(), MODE_BID);
      }
      else if(OrderType() == OP_SELL)
      {
         closePrice = MarketInfo(OrderSymbol(), MODE_ASK);
      }
      else
      {
         // Pending order - delete
         if(OrderDelete((int)ticket))
         {
            successfulCommands++;
            SendSuccessResponse(sock, requestId);
            return;
         }
         failedCommands++;
         SendErrorResponse(sock, requestId, STATUS_ERROR);
         return;
      }
      
      double lots = volume > 0 ? volume : OrderLots();
      
      if(OrderClose((int)ticket, lots, closePrice, MAX_SLIPPAGE, clrNONE))
      {
         successfulCommands++;
         SendSuccessResponse(sock, requestId);
      }
      else
      {
         failedCommands++;
         SendErrorResponse(sock, requestId, STATUS_REJECTED);
      }
   }
   else
   {
      failedCommands++;
      SendErrorResponse(sock, requestId, STATUS_INVALID);
   }
}

//+------------------------------------------------------------------+
//| Modify order                                                       |
//+------------------------------------------------------------------+
void ModifyOrder(int sock, ulong requestId, uchar& payload[])
{
   if(ArraySize(payload) < 24)
   {
      SendErrorResponse(sock, requestId, STATUS_INVALID);
      failedCommands++;
      return;
   }
   
   ulong ticket = ByteArrayToLong(payload, 0);
   double sl = ByteArrayToDouble(payload, 8);
   double tp = ByteArrayToDouble(payload, 16);
   
   if(OrderSelect((int)ticket, SELECT_BY_TICKET))
   {
      int digits = (int)MarketInfo(OrderSymbol(), MODE_DIGITS);
      sl = NormalizeDouble(sl, digits);
      tp = NormalizeDouble(tp, digits);
      
      if(OrderModify((int)ticket, OrderOpenPrice(), sl, tp, 0, clrNONE))
      {
         successfulCommands++;
         SendSuccessResponse(sock, requestId);
      }
      else
      {
         failedCommands++;
         SendErrorResponse(sock, requestId, STATUS_ERROR);
      }
   }
   else
   {
      failedCommands++;
      SendErrorResponse(sock, requestId, STATUS_INVALID);
   }
}

//+------------------------------------------------------------------+
//| Subscribe symbol                                                   |
//+------------------------------------------------------------------+
void SubscribeSymbol(uchar& payload[])
{
   if(ArraySize(payload) < 12) return;
   
   string symbol = ByteArrayToString(payload, 0, 12);
   symbol = StringTrimRight(symbol);
   
   // Check if already subscribed
   for(int i = 0; i < ArraySize(subscribedSymbols); i++)
   {
      if(subscribedSymbols[i] == symbol) return;
   }
   
   // Add to subscriptions
   int idx = ArraySize(subscribedSymbols);
   ArrayResize(subscribedSymbols, idx + 1);
   subscribedSymbols[idx] = symbol;
   
   SymbolSelect(symbol, true);
   Print("Subscribed to: ", symbol);
}

//+------------------------------------------------------------------+
//| Broadcast tick data                                                |
//+------------------------------------------------------------------+
void BroadcastTickData()
{
   for(int i = 0; i < ArraySize(subscribedSymbols); i++)
   {
      string symbol = subscribedSymbols[i];
      
      MqlTick tick;
      if(SymbolInfoTick(symbol, tick))
      {
         // Build binary tick message
         uchar tickData[52];
         
         StringToByteArrayFixed(symbol, tickData, 0, 12);
         
         int digits = (int)MarketInfo(symbol, MODE_DIGITS);
         double point = MarketInfo(symbol, MODE_POINT);
         
         DoubleToByteArray(tick.bid, tickData, 12);
         DoubleToByteArray(tick.ask, tickData, 20);
         DoubleToByteArray((tick.ask - tick.bid) / point, tickData, 28);
         LongToByteArray(tick.volume, tickData, 36);
         LongToByteArray(tick.time_msc * 1000, tickData, 44);
         
         // Broadcast to all connected clients
         for(int j = 0; j < ArraySize(clientSockets); j++)
         {
            if(clientSockets[j] != INVALID_SOCKET)
            {
               // Build response header
               uchar response[63];
               response[0] = STATUS_OK;
               
               ulong requestId = 0;
               for(int k = 0; k < 8; k++)
               {
                  response[1 + k] = 0;
               }
               
               response[9] = 52;  // payload length
               response[10] = 0;
               
               // Copy tick data
               for(int k = 0; k < 52; k++)
               {
                  response[11 + k] = tickData[k];
               }
               
               string sendStr = "";
               for(int k = 0; k < 63; k++)
               {
                  sendStr += CharToString(response[k]);
               }
               
               send(clientSockets[j], sendStr, 63, 0);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Helper: String to byte array                                       |
//+------------------------------------------------------------------+
void StringToByteArray(string str, uchar& arr[])
{
   int len = StringLen(str);
   ArrayResize(arr, len);
   for(int i = 0; i < len; i++)
   {
      arr[i] = (uchar)StringGetCharacter(str, i);
   }
}

//+------------------------------------------------------------------+
//| Helper: String to byte array fixed size                            |
//+------------------------------------------------------------------+
void StringToByteArrayFixed(string str, uchar& arr[], int offset, int size)
{
   int len = StringLen(str);
   for(int i = 0; i < size; i++)
   {
      if(i < len)
      {
         arr[offset + i] = (uchar)StringGetCharacter(str, i);
      }
      else
      {
         arr[offset + i] = 0;
      }
   }
}

//+------------------------------------------------------------------+
//| Helper: Byte array to string                                       |
//+------------------------------------------------------------------+
string ByteArrayToString(uchar& arr[], int offset, int size)
{
   string result = "";
   for(int i = 0; i < size; i++)
   {
      if(arr[offset + i] == 0) break;
      result += CharToString(arr[offset + i]);
   }
   return result;
}

//+------------------------------------------------------------------+
//| Helper: Double to byte array                                       |
//+------------------------------------------------------------------+
void DoubleToByteArray(double value, uchar& arr[], int offset = 0)
{
   // IEEE 754 double = 8 bytes, little-endian
   // MQL4 doesn't have direct conversion, use union-like approach
   long bits;
   memcpy(bits, value, 8);
   
   for(int i = 0; i < 8; i++)
   {
      arr[offset + i] = (uchar)((bits >> (i * 8)) & 0xFF);
   }
}

//+------------------------------------------------------------------+
//| Helper: Byte array to double                                       |
//+------------------------------------------------------------------+
double ByteArrayToDouble(uchar& arr[], int offset)
{
   long bits = 0;
   for(int i = 0; i < 8; i++)
   {
      bits |= ((long)arr[offset + i]) << (i * 8);
   }
   
   double result;
   memcpy(result, bits, 8);
   return result;
}

//+------------------------------------------------------------------+
//| Helper: Long to byte array                                         |
//+------------------------------------------------------------------+
void LongToByteArray(long value, uchar& arr[], int offset)
{
   for(int i = 0; i < 8; i++)
   {
      arr[offset + i] = (uchar)((value >> (i * 8)) & 0xFF);
   }
}

//+------------------------------------------------------------------+
//| Helper: Byte array to long                                         |
//+------------------------------------------------------------------+
long ByteArrayToLong(uchar& arr[], int offset)
{
   long result = 0;
   for(int i = 0; i < 8; i++)
   {
      result |= ((long)arr[offset + i]) << (i * 8);
   }
   return result;
}

//+------------------------------------------------------------------+
//| Helper: Int to byte array                                          |
//+------------------------------------------------------------------+
void IntToByteArray(int value, uchar& arr[], int offset)
{
   for(int i = 0; i < 4; i++)
   {
      arr[offset + i] = (uchar)((value >> (i * 8)) & 0xFF);
   }
}

//+------------------------------------------------------------------+
//| Helper: Byte array to int                                          |
//+------------------------------------------------------------------+
int ByteArrayToInt(uchar& arr[], int offset)
{
   int result = 0;
   for(int i = 0; i < 4; i++)
   {
      result |= ((int)arr[offset + i]) << (i * 8);
   }
   return result;
}
//+------------------------------------------------------------------+
