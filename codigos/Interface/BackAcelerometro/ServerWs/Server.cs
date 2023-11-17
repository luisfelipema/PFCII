using System.Transactions;
using System.Xml;
using ServerWebSocket.Entities;

namespace ServerWs;

using System.Collections.Concurrent;
using System.Diagnostics;
using System.Net;
using System.Net.WebSockets;
using System.Text;

public class ServerWs : IDisposable
{
    private static readonly HttpListener Listener = new ();
    private static readonly ConcurrentDictionary<string, List<HttpListenerWebSocketContext>> ConnectedClients = new();
    
    public ServerWs(int listenerPort = 8080, bool ssl = false)
    {
        var listenerHostname = Debugger.IsAttached ? "localhost" : "*";

        if (listenerPort < 0) 
            throw new ArgumentOutOfRangeException(nameof(listenerPort));

        var listenerPrefix = ssl ? "https://" + listenerHostname + ":" + listenerPort + "/" : "http://" + listenerHostname + ":" + listenerPort + "/";
        
        Listener.Prefixes.Add(listenerPrefix);
    }
    
    public async Task Start()
    {
        if (Listener.IsListening) 
            throw new InvalidOperationException("ServerWebSocket server is already running.");
        
        Listener.Start();

        await AcceptConnections();
    }

    private static async Task AcceptConnections()
    {
        while(true)
        {
            try
            {
                var context = await Listener.GetContextAsync();
                if (context.Request.IsWebSocketRequest)
                {
                    await Task.Run(() =>
                    {
                        var cntxt = context.AcceptWebSocketAsync(null).ConfigureAwait(true).GetAwaiter().GetResult();
                        _ = Task.Run(() => ProcessWebSocketRequest(cntxt));
                    });
                }
                else
                {
                    context.Response.StatusCode = (int)HttpStatusCode.BadRequest;
                    context.Response.Close();
                }
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
            }
        }
    }

    private static Task DisconnectConnection()
    {
        try
        {
            foreach (var (key, value) in ListConnections())
            {
                value.RemoveAll(s => s.WebSocket.State == WebSocketState.Closed);
                if (value.Count == 0) TryRemoveConnection(key);
            }
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
        }

        return Task.CompletedTask;
    }

    private static async Task ProcessWebSocketRequest(HttpListenerWebSocketContext md)
    {
        var buff = new byte[2048];
        while(md.WebSocket.State is WebSocketState.Open or WebSocketState.Connecting)
        {
            var receiveResult = md.WebSocket.ReceiveAsync(new ArraySegment<byte>(buff), CancellationToken.None).ConfigureAwait(true).GetAwaiter().GetResult();

            if (receiveResult.MessageType == WebSocketMessageType.Close)
            {
                await md.WebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, CancellationToken.None);
                await DisconnectConnection();
                continue;
            }

            try
            {
                var json = Encoding.UTF8.GetString(buff, 0, receiveResult.Count);

                if(message is null)
                    continue;

                switch (message!.Header.Topic)
                {
                    case TopicMessage.Register:

                        // TryAddConnection(topic, md);
                        continue;
                    
                    case TopicMessage.Client:
                        
                        continue;
                    
                    default:
                        throw new ArgumentOutOfRangeException();
                }
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
            }
        }
    }
    public static async Task SendMessage(string user = "", string device = "", string message = "")
    {
        try
        {
            var sender = !string.IsNullOrEmpty(device) ? user + "_" + device : user;
            var connection = ConnectedClients.FirstOrDefault(k => k.Key == sender);
            
            if (string.IsNullOrEmpty(connection.Key)) return;

            var cs = connection.Value.Where(a => a.WebSocket.State == WebSocketState.Open).ToList();
            
            // cs.ForEach(c => 
            //     c.WebSocket.SendAsync(new ArraySegment<byte>(null, WebSocketMessageType.Text, true, CancellationToken.None));

        }
        catch (Exception e)
        {
            Console.WriteLine(e);
        }
    }

    private static bool TryAddConnection(string guid, HttpListenerWebSocketContext connectionMetadata)
    {
        var connection = ListConnections().FirstOrDefault(s => s.Key == guid);
        if (string.IsNullOrEmpty(connection.Key))
            return ConnectedClients.TryAdd(guid, new(){connectionMetadata});
        else
        {
            connection.Value.Add(connectionMetadata);
            return true;
        }
    }

    private static bool TryRemoveConnection(string id)
    {
        return ConnectedClients.TryRemove(id, out _);
    }

    private static List<KeyValuePair<string, List<HttpListenerWebSocketContext>>> ListConnections()
    {
        return ConnectedClients.ToList();
    }

    public void Dispose()
    {
        if (Listener.IsListening) 
            Listener.Stop();
            
        Listener.Close();
    }
    
}