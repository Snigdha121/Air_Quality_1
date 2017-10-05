HARIOT Grafana Docker Image

 * Current Version: 4.5.2
 * Current URL: http://eclipse.usc.edu:10001

Grafana has a web interfaces which makes setup easier. We are simply launching
the default Grafana image. Upgrade to the latest image when needed. We are
using persistent storage so make sure the old formats are compatible with
the newer versions of Grafana before upgrading.

    docker run -d --restart="always" --name=iotsc-grafana -p 10001:3000 -v /home/iotsc/iotsc-grafana-data:/var/lib/grafana grafana/grafana:4.5.2

The `/home/iotsc/iotsc-grafana-data` folder is used for persistent storage
and the container is set to always restart.

