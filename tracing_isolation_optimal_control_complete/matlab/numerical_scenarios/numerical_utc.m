function value = numerical_utc()
% 不依赖主机本地时区。
value=char(datetime('now','TimeZone','UTC','Format',"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"));
end
