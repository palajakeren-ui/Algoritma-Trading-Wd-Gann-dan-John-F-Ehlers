//+------------------------------------------------------------------+
//|                                            GQ_ZMQ_Bridge.mq4      |
//|                                    Gann-Ehlers Trading System     |
//|                                    ZMQ Bridge Expert Advisor      |
//+------------------------------------------------------------------+
#property copyright "Gann-Ehlers Trading System"
#property link      "https://github.com/gann-ehlers"
#property version   "3.00"
#property strict
#property description "ZeroMQ Bridge EA for MetaTrader 4"

//--- ZMQ Library (download from: https://github.com/dingmaotu/mql-zmq)
#include <Zmq/Zmq.mqh>

//--- Input parameters
input string   ZMQ_Settings = "=== ZMQ Settings ===";
input string   REQ_HOST = "localhost";
input int      REQ_PORT = 5555;
input string   SUB_HOST = "localhost";
input int      PUB_PORT = 5556;
input int      HEARTBEAT_MS = 5000;

input string   Trading_Settings = "=== Trading Settings ===";
input int      MAGIC_NUMBER = 123456;
input string   ORDER_COMMENT = "GQ_BOT";
input int      MAX_SLIPPAGE = 3;

input string   Streaming_Settings = "=== Streaming Settings ===";
input bool     STREAM_TICKS = true;
input bool     STREAM_POSITIONS = true;
input string   SYMBOLS_TO_STREAM = "EURUSD,GBPUSD,USDJPY,XAUUSD";

//--- Global variables
Context context;
Socket reqSocket;
Socket pubSocket;

datetime lastHeartbeat;
string subscribedSymbols[];
bool isRunning = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
    context = Context();
    
    reqSocket = context.Socket(ZMQ_REP);
    string reqAddr = "tcp://*:" + IntegerToString(REQ_PORT);
    if(!reqSocket.Bind(reqAddr))
    {
        Print("Failed to bind REQ socket: ", reqSocket.LastError());
        return INIT_FAILED;
    }
    Print("REQ socket bound to: ", reqAddr);
    
    pubSocket = context.Socket(ZMQ_PUB);
    string pubAddr = "tcp://*:" + IntegerToString(PUB_PORT);
    if(!pubSocket.Bind(pubAddr))
    {
        Print("Failed to bind PUB socket: ", pubSocket.LastError());
        return INIT_FAILED;
    }
    Print("PUB socket bound to: ", pubAddr);
    
    ParseSymbols(SYMBOLS_TO_STREAM);
    
    reqSocket.SetSendHighWaterMark(1000);
    reqSocket.SetReceiveHighWaterMark(1000);
    pubSocket.SetSendHighWaterMark(10000);
    
    isRunning = true;
    lastHeartbeat = TimeCurrent();
    
    Print("GQ ZMQ Bridge EA initialized successfully");
    Print("Account: ", AccountNumber(), " Balance: ", AccountBalance());
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    isRunning = false;
    
    if(reqSocket.IsValid())
    {
        reqSocket.Unbind("tcp://*:" + IntegerToString(REQ_PORT));
        reqSocket.Close();
    }
    
    if(pubSocket.IsValid())
    {
        pubSocket.Unbind("tcp://*:" + IntegerToString(PUB_PORT));
        pubSocket.Close();
    }
    
    context.Term();
    
    Print("GQ ZMQ Bridge EA stopped. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
    if(!isRunning) return;
    
    ProcessCommands();
    
    if(STREAM_TICKS)
    {
        StreamTickData();
    }
    
    if(TimeCurrent() - lastHeartbeat > HEARTBEAT_MS / 1000)
    {
        lastHeartbeat = TimeCurrent();
        SendHeartbeat();
    }
}

//+------------------------------------------------------------------+
//| Process incoming ZMQ commands                                      |
//+------------------------------------------------------------------+
void ProcessCommands()
{
    ZmqMsg request;
    ZmqMsg reply;
    
    if(reqSocket.Recv(request, ZMQ_DONTWAIT))
    {
        string cmdStr = request.GetData();
        string response = ProcessJSONCommand(cmdStr);
        
        reply = ZmqMsg(response);
        reqSocket.Send(reply);
    }
}

//+------------------------------------------------------------------+
//| Process JSON command                                               |
//+------------------------------------------------------------------+
string ProcessJSONCommand(string cmdStr)
{
    string command = GetJsonValue(cmdStr, "command");
    string params = GetJsonValue(cmdStr, "params");
    
    if(command == "PING")
    {
        return "{\"status\":\"ok\",\"command\":\"PONG\",\"timestamp\":" + IntegerToString(TimeCurrent()) + "}";
    }
    else if(command == "ACCOUNT_INFO")
    {
        return GetAccountInfoJSON();
    }
    else if(command == "BALANCE")
    {
        return "{\"status\":\"ok\",\"balance\":" + DoubleToString(AccountBalance(), 2) + "}";
    }
    else if(command == "EQUITY")
    {
        return "{\"status\":\"ok\",\"equity\":" + DoubleToString(AccountEquity(), 2) + "}";
    }
    else if(command == "SYMBOL_INFO")
    {
        string symbol = GetJsonValue(params, "symbol");
        return GetSymbolInfoJSON(symbol);
    }
    else if(command == "TICK")
    {
        string symbol = GetJsonValue(params, "symbol");
        return GetTickJSON(symbol);
    }
    else if(command == "BARS")
    {
        return GetBarsJSON(params);
    }
    else if(command == "POSITIONS")
    {
        return GetPositionsJSON();
    }
    else if(command == "ORDER_SEND")
    {
        return ExecuteOrder(params);
    }
    else if(command == "POSITION_MODIFY")
    {
        return ModifyPosition(params);
    }
    else if(command == "POSITION_CLOSE")
    {
        return ClosePosition(params);
    }
    
    return "{\"status\":\"error\",\"message\":\"Unknown command: " + command + "\"}";
}

//+------------------------------------------------------------------+
//| Get Account Info JSON                                              |
//+------------------------------------------------------------------+
string GetAccountInfoJSON()
{
    string json = "{";
    json += "\"status\":\"ok\",";
    json += "\"account\":{";
    json += "\"login\":" + IntegerToString(AccountNumber()) + ",";
    json += "\"name\":\"" + AccountName() + "\",";
    json += "\"server\":\"" + AccountServer() + "\",";
    json += "\"currency\":\"" + AccountCurrency() + "\",";
    json += "\"balance\":" + DoubleToString(AccountBalance(), 2) + ",";
    json += "\"equity\":" + DoubleToString(AccountEquity(), 2) + ",";
    json += "\"margin\":" + DoubleToString(AccountMargin(), 2) + ",";
    json += "\"free_margin\":" + DoubleToString(AccountFreeMargin(), 2) + ",";
    json += "\"margin_level\":" + DoubleToString(AccountMarginLevel(), 2) + ",";
    json += "\"leverage\":" + IntegerToString(AccountLeverage()) + ",";
    json += "\"profit\":" + DoubleToString(AccountProfit(), 2);
    json += "}}";
    
    return json;
}

//+------------------------------------------------------------------+
//| Get Symbol Info JSON                                               |
//+------------------------------------------------------------------+
string GetSymbolInfoJSON(string symbol)
{
    if(!SymbolSelect(symbol, true))
    {
        return "{\"status\":\"error\",\"message\":\"Symbol not found: " + symbol + "\"}";
    }
    
    string json = "{";
    json += "\"status\":\"ok\",";
    json += "\"info\":{";
    json += "\"symbol\":\"" + symbol + "\",";
    json += "\"bid\":" + DoubleToString(MarketInfo(symbol, MODE_BID), (int)MarketInfo(symbol, MODE_DIGITS)) + ",";
    json += "\"ask\":" + DoubleToString(MarketInfo(symbol, MODE_ASK), (int)MarketInfo(symbol, MODE_DIGITS)) + ",";
    json += "\"spread\":" + DoubleToString(MarketInfo(symbol, MODE_SPREAD), 0) + ",";
    json += "\"digits\":" + IntegerToString((int)MarketInfo(symbol, MODE_DIGITS)) + ",";
    json += "\"point\":" + DoubleToString(MarketInfo(symbol, MODE_POINT), (int)MarketInfo(symbol, MODE_DIGITS)) + ",";
    json += "\"lot_min\":" + DoubleToString(MarketInfo(symbol, MODE_MINLOT), 2) + ",";
    json += "\"lot_max\":" + DoubleToString(MarketInfo(symbol, MODE_MAXLOT), 2) + ",";
    json += "\"lot_step\":" + DoubleToString(MarketInfo(symbol, MODE_LOTSTEP), 2);
    json += "}}";
    
    return json;
}

//+------------------------------------------------------------------+
//| Get Tick JSON                                                      |
//+------------------------------------------------------------------+
string GetTickJSON(string symbol)
{
    if(!SymbolSelect(symbol, true))
    {
        return "{\"status\":\"error\",\"message\":\"Symbol not found\"}";
    }
    
    MqlTick tick;
    if(!SymbolInfoTick(symbol, tick))
    {
        return "{\"status\":\"error\",\"message\":\"Failed to get tick\"}";
    }
    
    string json = "{";
    json += "\"status\":\"ok\",";
    json += "\"tick\":{";
    json += "\"symbol\":\"" + symbol + "\",";
    json += "\"bid\":" + DoubleToString(tick.bid, (int)MarketInfo(symbol, MODE_DIGITS)) + ",";
    json += "\"ask\":" + DoubleToString(tick.ask, (int)MarketInfo(symbol, MODE_DIGITS)) + ",";
    json += "\"spread\":" + DoubleToString((tick.ask - tick.bid) / MarketInfo(symbol, MODE_POINT), 0) + ",";
    json += "\"time\":" + IntegerToString(tick.time) + ",";
    json += "\"volume\":" + IntegerToString(tick.volume);
    json += "}}";
    
    return json;
}

//+------------------------------------------------------------------+
//| Get Bars JSON                                                      |
//+------------------------------------------------------------------+
string GetBarsJSON(string params)
{
    string symbol = GetJsonValue(params, "symbol");
    string tf = GetJsonValue(params, "timeframe");
    int count = (int)StringToInteger(GetJsonValue(params, "count"));
    
    if(count <= 0 || count > 10000) count = 1000;
    
    int timeframe = PERIOD_H1;
    if(tf == "M1") timeframe = PERIOD_M1;
    else if(tf == "M5") timeframe = PERIOD_M5;
    else if(tf == "M15") timeframe = PERIOD_M15;
    else if(tf == "M30") timeframe = PERIOD_M30;
    else if(tf == "H1") timeframe = PERIOD_H1;
    else if(tf == "H4") timeframe = PERIOD_H4;
    else if(tf == "D1") timeframe = PERIOD_D1;
    else if(tf == "W1") timeframe = PERIOD_W1;
    
    if(!SymbolSelect(symbol, true))
    {
        return "{\"status\":\"error\",\"message\":\"Symbol not found\"}";
    }
    
    string json = "{\"status\":\"ok\",\"bars\":[";
    
    int digits = (int)MarketInfo(symbol, MODE_DIGITS);
    
    for(int i = count - 1; i >= 0; i--)
    {
        if(i < count - 1) json += ",";
        
        json += "{";
        json += "\"time\":" + IntegerToString(iTime(symbol, timeframe, i)) + ",";
        json += "\"open\":" + DoubleToString(iOpen(symbol, timeframe, i), digits) + ",";
        json += "\"high\":" + DoubleToString(iHigh(symbol, timeframe, i), digits) + ",";
        json += "\"low\":" + DoubleToString(iLow(symbol, timeframe, i), digits) + ",";
        json += "\"close\":" + DoubleToString(iClose(symbol, timeframe, i), digits) + ",";
        json += "\"volume\":" + IntegerToString(iVolume(symbol, timeframe, i));
        json += "}";
    }
    
    json += "]}";
    
    return json;
}

//+------------------------------------------------------------------+
//| Get Positions JSON                                                 |
//+------------------------------------------------------------------+
string GetPositionsJSON()
{
    string json = "{\"status\":\"ok\",\"positions\":[";
    
    int total = OrdersTotal();
    
    for(int i = 0; i < total; i++)
    {
        if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if(i > 0) json += ",";
            
            json += "{";
            json += "\"ticket\":" + IntegerToString(OrderTicket()) + ",";
            json += "\"symbol\":\"" + OrderSymbol() + "\",";
            json += "\"type\":" + IntegerToString(OrderType()) + ",";
            json += "\"volume\":" + DoubleToString(OrderLots(), 2) + ",";
            json += "\"open_price\":" + DoubleToString(OrderOpenPrice(), (int)MarketInfo(OrderSymbol(), MODE_DIGITS)) + ",";
            json += "\"sl\":" + DoubleToString(OrderStopLoss(), (int)MarketInfo(OrderSymbol(), MODE_DIGITS)) + ",";
            json += "\"tp\":" + DoubleToString(OrderTakeProfit(), (int)MarketInfo(OrderSymbol(), MODE_DIGITS)) + ",";
            json += "\"profit\":" + DoubleToString(OrderProfit(), 2) + ",";
            json += "\"swap\":" + DoubleToString(OrderSwap(), 2) + ",";
            json += "\"commission\":" + DoubleToString(OrderCommission(), 2) + ",";
            json += "\"comment\":\"" + OrderComment() + "\",";
            json += "\"magic\":" + IntegerToString(OrderMagicNumber()) + ",";
            json += "\"open_time\":" + IntegerToString(OrderOpenTime());
            json += "}";
        }
    }
    
    json += "]}";
    
    return json;
}

//+------------------------------------------------------------------+
//| Execute Order                                                      |
//+------------------------------------------------------------------+
string ExecuteOrder(string params)
{
    string symbol = GetJsonValue(params, "symbol");
    string side = GetJsonValue(params, "side");
    double volume = StringToDouble(GetJsonValue(params, "volume"));
    string orderType = GetJsonValue(params, "type");
    double price = StringToDouble(GetJsonValue(params, "price"));
    double sl = StringToDouble(GetJsonValue(params, "sl"));
    double tp = StringToDouble(GetJsonValue(params, "tp"));
    int slippage = (int)StringToInteger(GetJsonValue(params, "slippage"));
    int magic = (int)StringToInteger(GetJsonValue(params, "magic"));
    string comment = GetJsonValue(params, "comment");
    
    if(slippage == 0) slippage = MAX_SLIPPAGE;
    if(magic == 0) magic = MAGIC_NUMBER;
    if(comment == "") comment = ORDER_COMMENT;
    
    int cmd;
    double execPrice;
    
    if(orderType == "MARKET")
    {
        if(side == "BUY")
        {
            cmd = OP_BUY;
            execPrice = MarketInfo(symbol, MODE_ASK);
        }
        else
        {
            cmd = OP_SELL;
            execPrice = MarketInfo(symbol, MODE_BID);
        }
    }
    else if(orderType == "LIMIT")
    {
        if(side == "BUY")
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
    else if(orderType == "STOP")
    {
        if(side == "BUY")
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
    
    int digits = (int)MarketInfo(symbol, MODE_DIGITS);
    execPrice = NormalizeDouble(execPrice, digits);
    sl = NormalizeDouble(sl, digits);
    tp = NormalizeDouble(tp, digits);
    
    int ticket = OrderSend(symbol, cmd, volume, execPrice, slippage, sl, tp, comment, magic, 0, clrNONE);
    
    if(ticket > 0)
    {
        string json = "{";
        json += "\"status\":\"ok\",";
        json += "\"ticket\":" + IntegerToString(ticket) + ",";
        json += "\"symbol\":\"" + symbol + "\",";
        json += "\"side\":\"" + side + "\",";
        json += "\"type\":\"" + orderType + "\",";
        json += "\"volume\":" + DoubleToString(volume, 2) + ",";
        json += "\"price\":" + DoubleToString(execPrice, digits) + ",";
        json += "\"sl\":" + DoubleToString(sl, digits) + ",";
        json += "\"tp\":" + DoubleToString(tp, digits);
        json += "}";
        
        return json;
    }
    else
    {
        int error = GetLastError();
        return "{\"status\":\"error\",\"message\":\"Order failed\",\"error\":" + IntegerToString(error) + "}";
    }
}

//+------------------------------------------------------------------+
//| Modify Position                                                    |
//+------------------------------------------------------------------+
string ModifyPosition(string params)
{
    int ticket = (int)StringToInteger(GetJsonValue(params, "ticket"));
    double sl = StringToDouble(GetJsonValue(params, "sl"));
    double tp = StringToDouble(GetJsonValue(params, "tp"));
    
    if(OrderSelect(ticket, SELECT_BY_TICKET))
    {
        int digits = (int)MarketInfo(OrderSymbol(), MODE_DIGITS);
        sl = NormalizeDouble(sl, digits);
        tp = NormalizeDouble(tp, digits);
        
        if(OrderModify(ticket, OrderOpenPrice(), sl, tp, 0, clrNONE))
        {
            return "{\"status\":\"ok\",\"ticket\":" + IntegerToString(ticket) + "}";
        }
        else
        {
            int error = GetLastError();
            return "{\"status\":\"error\",\"message\":\"Modify failed\",\"error\":" + IntegerToString(error) + "}";
        }
    }
    
    return "{\"status\":\"error\",\"message\":\"Position not found\"}";
}

//+------------------------------------------------------------------+
//| Close Position                                                     |
//+------------------------------------------------------------------+
string ClosePosition(string params)
{
    int ticket = (int)StringToInteger(GetJsonValue(params, "ticket"));
    double volume = StringToDouble(GetJsonValue(params, "volume"));
    
    if(OrderSelect(ticket, SELECT_BY_TICKET))
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
            if(OrderDelete(ticket))
            {
                return "{\"status\":\"ok\",\"ticket\":" + IntegerToString(ticket) + "}";
            }
            return "{\"status\":\"error\",\"message\":\"Delete failed\"}";
        }
        
        double lots = volume > 0 ? volume : OrderLots();
        
        if(OrderClose(ticket, lots, closePrice, MAX_SLIPPAGE, clrNONE))
        {
            string json = "{";
            json += "\"status\":\"ok\",";
            json += "\"ticket\":" + IntegerToString(ticket) + ",";
            json += "\"close_price\":" + DoubleToString(closePrice, (int)MarketInfo(OrderSymbol(), MODE_DIGITS)) + ",";
            json += "\"profit\":" + DoubleToString(OrderProfit(), 2);
            json += "}";
            
            return json;
        }
        else
        {
            int error = GetLastError();
            return "{\"status\":\"error\",\"message\":\"Close failed\",\"error\":" + IntegerToString(error) + "}";
        }
    }
    
    return "{\"status\":\"error\",\"message\":\"Position not found\"}";
}

//+------------------------------------------------------------------+
//| Stream Tick Data                                                   |
//+------------------------------------------------------------------+
void StreamTickData()
{
    for(int i = 0; i < ArraySize(subscribedSymbols); i++)
    {
        string symbol = subscribedSymbols[i];
        
        MqlTick tick;
        if(SymbolInfoTick(symbol, tick))
        {
            string json = "{";
            json += "\"type\":\"TICK\",";
            json += "\"symbol\":\"" + symbol + "\",";
            json += "\"bid\":" + DoubleToString(tick.bid, (int)MarketInfo(symbol, MODE_DIGITS)) + ",";
            json += "\"ask\":" + DoubleToString(tick.ask, (int)MarketInfo(symbol, MODE_DIGITS)) + ",";
            json += "\"spread\":" + DoubleToString((tick.ask - tick.bid) / MarketInfo(symbol, MODE_POINT), 0) + ",";
            json += "\"time\":" + IntegerToString(tick.time) + ",";
            json += "\"volume\":" + IntegerToString(tick.volume);
            json += "}";
            
            ZmqMsg msg = ZmqMsg(json);
            pubSocket.Send(msg, ZMQ_DONTWAIT);
        }
    }
}

//+------------------------------------------------------------------+
//| Send Heartbeat                                                     |
//+------------------------------------------------------------------+
void SendHeartbeat()
{
    string json = "{";
    json += "\"type\":\"HEARTBEAT\",";
    json += "\"time\":" + IntegerToString(TimeCurrent()) + ",";
    json += "\"positions\":" + IntegerToString(OrdersTotal());
    json += "}";
    
    ZmqMsg msg = ZmqMsg(json);
    pubSocket.Send(msg, ZMQ_DONTWAIT);
}

//+------------------------------------------------------------------+
//| Parse Symbols                                                      |
//+------------------------------------------------------------------+
void ParseSymbols(string symbolsStr)
{
    string delimiter = ",";
    int start = 0;
    int count = 0;
    
    for(int i = 0; i < StringLen(symbolsStr); i++)
    {
        if(StringGetCharacter(symbolsStr, i) == 44) count++;
    }
    
    ArrayResize(subscribedSymbols, count + 1);
    
    int idx = 0;
    int pos = StringFind(symbolsStr, delimiter, start);
    
    while(pos != -1)
    {
        string symbol = StringSubstr(symbolsStr, start, pos - start);
        symbol = StringTrimLeft(StringTrimRight(symbol));
        
        subscribedSymbols[idx] = symbol;
        SymbolSelect(symbol, true);
        idx++;
        
        start = pos + 1;
        pos = StringFind(symbolsStr, delimiter, start);
    }
    
    string lastSymbol = StringSubstr(symbolsStr, start);
    lastSymbol = StringTrimLeft(StringTrimRight(lastSymbol));
    
    if(StringLen(lastSymbol) > 0)
    {
        subscribedSymbols[idx] = lastSymbol;
        SymbolSelect(lastSymbol, true);
    }
    
    Print("Subscribed symbols: ", ArraySize(subscribedSymbols));
}

//+------------------------------------------------------------------+
//| Helper: Get JSON Value                                             |
//+------------------------------------------------------------------+
string GetJsonValue(string json, string key)
{
    string searchKey = "\"" + key + "\"";
    int keyPos = StringFind(json, searchKey);
    
    if(keyPos == -1) return "";
    
    int colonPos = StringFind(json, ":", keyPos);
    if(colonPos == -1) return "";
    
    int valueStart = colonPos + 1;
    
    while(valueStart < StringLen(json))
    {
        ushort ch = StringGetCharacter(json, valueStart);
        if(ch == 32 || ch == 9 || ch == 10 || ch == 13) valueStart++;
        else break;
    }
    
    ushort firstChar = StringGetCharacter(json, valueStart);
    
    if(firstChar == 34)
    {
        int endQuote = StringFind(json, "\"", valueStart + 1);
        if(endQuote > valueStart)
        {
            return StringSubstr(json, valueStart + 1, endQuote - valueStart - 1);
        }
    }
    else
    {
        int valueEnd = valueStart;
        while(valueEnd < StringLen(json))
        {
            ushort ch = StringGetCharacter(json, valueEnd);
            if(ch == 44 || ch == 125 || ch == 93 || ch == 32 || ch == 10 || ch == 13)
            {
                break;
            }
            valueEnd++;
        }
        
        return StringSubstr(json, valueStart, valueEnd - valueStart);
    }
    
    return "";
}

//+------------------------------------------------------------------+
//| Trade Transaction Handler                                          |
//+------------------------------------------------------------------+
void OnTrade()
{
    if(!STREAM_POSITIONS) return;
    
    string json = GetPositionsJSON();
    json = StringReplace(json, "\"status\":\"ok\"", "\"type\":\"POSITION_UPDATE\"");
    
    ZmqMsg msg = ZmqMsg(json);
    pubSocket.Send(msg, ZMQ_DONTWAIT);
}
//+------------------------------------------------------------------+
